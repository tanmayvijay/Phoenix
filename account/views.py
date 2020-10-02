from django.shortcuts import render, HttpResponseRedirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import authenticate, login
from .forms import LoginForm, UserRegistrationForm, UserEditForm, ProfileEditForm
from django.contrib.auth.decorators import login_required
from .models import Profile
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST
from common.decorators import ajax_required
from .models import Contact
from actions.utils import create_action
from actions.models import Action

# Create your views here.

def social_media_register(request):
	
	if request.user.is_authenticated:
		return HttpResponseRedirect(reverse_lazy('home'))
	if request.method == 'POST':
		user_form = UserRegistrationForm(data=request.POST)
		if user_form.is_valid():
			new_user = user_form.save(commit=False)
			

			new_user.set_password(user_form.cleaned_data['password1'])
			new_user.save()


			return HttpResponse("Success refister!")

	else:
		user_form = UserRegistrationForm()


	return render(request, 'accounts/register.html', context={'user_form':user_form})




def social_media_login_view(request):
	
	if request.user.is_authenticated:
		return HttpResponseRedirect(reverse_lazy('homepage'))
	if request.method == 'POST':
		login_form = LoginForm(data=request.POST)

		if login_form.is_valid():
			cd = login_form.cleaned_data
			user = authenticate(request, username=cd['username'], password=cd['password'])
			if user is not None:
				if user.is_active:
					login(request, user)
					next_page = request.GET.get('next')

					if next_page:
						return HttpResponseRedirect(next_page)

					return HttpResponseRedirect(reverse_lazy('homepage'))

				else:
					return HttpResponse("Account Terminated!")

			else:
				return HttpResponse("User Doesnt exist!")
		
	else:
		login_form = LoginForm()
	return render(request, 'accounts/login.html', context={'login_form': login_form})


@login_required
def social_profile_view(request, username):

	user = get_object_or_404(User, username=username)
	follow = False
	try:
		if request.user.profile.following.get(user=user):
			follow = True
	except Exception as e:
		print(e)
	
	return render(request, 'accounts/profile_page.html', {'user': user, 'follow': follow})

@login_required
def edit_profile_view(request, username):
	if not username == request.user.username:
		return HttpResponseRedirect(reverse_lazy('accounts:profile', args=[username]))

	if request.method == 'POST':
		edit_form = EditProfileForm(data=request.POST)
		if edit_form.is_valid():
			cd = edit_form.cleaned_data
			user = request.user
			user.first_name = cd['first_name']
			user.last_name = cd['last_name']
			user.email = cd['email']
			user.username = cd['username']

			user.profile.mob_no = cd['mob_no']
			user.profile.save()

			user.save()

			return HttpResponseRedirect(reverse_lazy('accounts:profile', kwargs={'username': user.username}))
	else:
		edit_form = EditProfileForm()

	return render(request, 'accounts/edit_profile.html', {'edit_form':edit_form})
	
@login_required
def follow_view(request, username):
	if username == request.user.username:
		return HttpResponseRedirect(reverse_lazy('accounts:profile', args=[username]))


	user_to_follow = get_object_or_404(User, username=username)
	current_user = request.user	

	current_user.profile.following.add(user_to_follow.profile)

	current_user.save()

	return HttpResponseRedirect(reverse_lazy('accounts:profile', kwargs={'username': username}))

@login_required
def unfollow_view(request, username):
	# to prevent unfollowing self
	if username == request.user.username:
		return HttpResponseRedirect(reverse_lazy('accounts:profile', args=[username]))

		
	user_to_unfollow = get_object_or_404(User, username=username)
	current_user = request.user

	try:
		if current_user.profile.following.get(user=user_to_unfollow):
			current_user.profile.following.remove(user_to_unfollow.profile)
			current_user.save()
	except Exception as e:
		print(e)

	return HttpResponseRedirect(reverse_lazy('accounts:profile', kwargs={'username': username}))




# showing suggested people to follow
@login_required
def accounts_home(request):

	suggested_users = User.objects.exclude(profile__followers__user__username__contains=request.user.username)
	users = request.user.profile.following.all()

	users = User.objects.filter(profile__following__user__username__contains=request.user.username)

	type_of_users = "Suggested Users"
	

	
	return render(request, 'accounts/home.html', {'users': suggested_users, 'type_of_users':type_of_users})




# showing followers
@login_required
def followers(request):

	follower_users = User.objects.filter(profile__following__user__username__contains=request.user.username)

	type_of_users = "Followers"
	

	
	return render(request, 'accounts/home.html', {'users': follower_users, 'type_of_users':type_of_users})





# showing followed people
@login_required
def following(request):

	following_users = request.user.profile.following.all()

	type_of_users = "Following"
	
	return render(request, 'accounts/home.html', {'users': following_users, 'type_of_users':type_of_users})

def user_login(request):
	form = None
	if request.method == 'POST':
		form = LoginForm(request.POST)

		if form.is_valid():
			cd = form.cleaned_data
			user = authenticate(request, username = cd['username'], password=cd['password'])

			if user is not None:
				if user.is_active:
					login(request, user)
					return HttpResponse('Authenticated Successfully!')
				else:
					return HttpResponse('Disabled Account!')

			else:
				return HttpResponse('Invalid account!')
	else:
		form = LoginForm()

	return render(request, 'account/login.html', {'form': form})




def register(request):
	if request.method == 'POST':
		user_form = UserRegistrationForm(request.POST)

		if user_form.is_valid():
			new_user = user_form.save(commit=False)

			new_user.set_password(user_form.cleaned_data['password'])

			new_user.save()

			Profile.objects.create(user=new_user)

			create_action(new_user, 'has created an account')

			return render(request, 'account/register_done.html', {'new_user': new_user})
	else:
		user_form = UserRegistrationForm()

	return render(request, 'account/register.html', {'user_form': user_form})



@login_required
def edit(request):
	if request.method == 'POST':
		user_form = UserEditForm(instance=request.user, data=request.POST)

		profile_form = ProfileEditForm(instance=request.user.profile, data=request.POST, files=request.FILES)

		if user_form.is_valid() and profile_form.is_valid():
			user_form.save()
			profile_form.save()
			
			messages.success(request, 'Profile updted successfully')

			return HttpResponseRedirect(reverse_lazy('account:dashboard'))

		messages.error(request, 'Error updating your profile')
	else:

		user_form = UserEditForm(instance=request.user)
		profile_form = ProfileEditForm(instance=request.user.profile)


	return render(request, 'account/edit.html', {'user_form': user_form, 'profile_form': profile_form})





@login_required
def user_list(request):
	users = User.objects.filter(is_active=True)

	return render(request, 'account/list.html', {'section': 'people', 'users': users})


@login_required
def user_detail(request, username):
	user = get_object_or_404(User, username=username, is_active=True)

	return render(request, 'account/detail.html', {'section': 'people', 'user':user})




@ajax_required
@require_POST
@login_required
def user_follow(request):
    user_id = request.POST.get('id')
    action = request.POST.get('action')
    if user_id and action:
        try:
            user = User.objects.get(id=user_id)
            if action == 'follow':
                Contact.objects.get_or_create(user_from=request.user,
                                              user_to=user)
                create_action(request.user, 'is following', user)
            else:
                Contact.objects.filter(user_from=request.user,
                                       user_to=user).delete()
            return JsonResponse({'status':'ok'})
        except User.DoesNotExist:
            return JsonResponse({'status':'ko'})
    return JsonResponse({'status':'ko'})




@login_required
def dashboard(request):
	actions = Action.objects.exclude(user=request.user)
	following_ids = request.user.following.values_list('id', flat=True)

	if following_ids:
		actions = actions.filter(user_id__in=following_ids)

	actions = actions.select_related('user', 'user__profile').prefetch_related('target')[:10]


	return render(request, 'account/dashboard.html', {'section': 'dashboard', 'actions': actions})
