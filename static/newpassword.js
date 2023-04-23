function checking(){
    var password = document.querySelector('#passwordForm');
    console.log('success')
    console.log(password.type)
if ( password.getAttribute('type') == 'password'){
    password.setAttribute('type', 'text');
    console.log('text');
    }
else{
    password.setAttribute('type', 'password');
    console.log('password');
    }
}
