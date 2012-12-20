var onRoundReply = function(reply) {
    if (reply.state != null && reply.state != 'round') {
        location.reload(true);
    }

    $("span#curround").text(reply.curround);
    $("span#secondsremains").text(reply.secondsremains);
    if (reply.bestattempt != null) {
        $("span#bestattempt_word").text(reply.bestattempt.word);
        $("span#bestattempt_score").text(reply.bestattempt.score);
    }
    if (reply.lastattempt != null) {
        $("span#lastattempt_word").text(reply.lastattempt.word);
        $("span#lastattempt_score").text(reply.lastattempt.score);
    }
    if (reply.reason) {
        $("span#error").text(reply.reason);
    }
};

var onRestReply = function(reply) {
    if (reply.state != 'rest') {
        location.reload(true);
    }

    $("span#secondsremains").text(reply.secondsremains);
}

var updateRound = onRoundReply;

var sendRoundAttempt = function() {
    var word = $("input[name=word]").val();
    $.getJSON($SCRIPT_ROOT + "/json/attempt", {'word': word}, onRoundReply);
    $("input[name=word]").val('');
}

var drawCard = function(canvas, letter, score) {
    var margin = 10;
    var font = "Calibri";

    var ctx = canvas.getContext("2d");
    ctx.font="65px " + font;
    ctx.textBaseline = "middle";
    var dim = ctx.measureText(letter);
    var x = (canvas.width - dim.width) / 2;
    var y = canvas.height / 2 - margin;
    ctx.fillText(letter, x, y);

    ctx.textBaseline = "alphabetic";
    ctx.font="30px " + font;
    score = score.toString();
    dim = ctx.measureText(score);
    x = (canvas.width - dim.width) / 2;
    y = canvas.height - margin;
    ctx.fillText(score, x, y);
};
