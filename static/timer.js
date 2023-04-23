var date = document.getElementById('xuy').innerHTML.split('-');
console.log(date[0], date[1], date[2])
var deadline = new Date(date[0], date[1], date[2]).getTime();
var x = setInterval(function() {
var now = new Date().getTime();
var t = deadline - now;
var days = Math.floor(t / (1000 * 60 * 60 * 24));
var hours = Math.floor((t%(1000 * 60 * 60 * 24))/(1000 * 60 * 60));
var minutes = Math.floor((t % (1000 * 60 * 60)) / (1000 * 60));
var seconds = Math.floor((t % (1000 * 60)) / 1000);
document.getElementById("demo").innerHTML = days + " дн " 

+ hours + " ч " + minutes + " мин " + seconds + " сек ";
    if (t < 0) {
        clearInterval(x);
        document.getElementById("demo").innerHTML = "ПРОСРОЧЕН!!!";
    }
}, 1000);
