(function(){
	if (window.myBookmarklet !== undefined){
		myBookmarklet();
	}
	else{
		document.body.appendchild(document.createElement('script')).src='http://0bfae168.ngrok.io/static/js/bookmarklet.js?r='+Math.floor(Math.random()*99999999999999999999)
	}
})();