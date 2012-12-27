var updateTimer = function(totalseconds, secondsremains) {
    var timebar = document.getElementById('timeremainsbar');
    if (timebar) {
        var percents = 100.0 * secondsremains / totalseconds;
        timebar.style.width = percents.toString() + "%";
    }
    var span = $("span#secondsremains");
    if (span) {
        span.text(secondsremains);
    }
}

var onRoundReply = function(reply) {
    if (reply.state != null && reply.state != 'round') {
        location.reload(true);
    }

    $("span#curround").text(reply.curround);
    updateTimer(reply.secondstotal, reply.secondsremains);
    if (reply.bestattempt != null) {
        $("span#bestattempt_word").text(reply.bestattempt.word);
        $("span#bestattempt_score").text(reply.bestattempt.score);
    }
    if (reply.lastattempt != null) {
        $("span#lastattempt_word").text(reply.lastattempt.word);
        $("span#lastattempt_score").text(reply.lastattempt.score);
    }
    if (reply.reason) {
        $("#error").removeClass("invisible");
        $("#error").text(reply.reason);
    } 
};

var onRestReply = function(reply) {
    if (reply.state != 'rest') {
        location.reload(true);
    }
    updateTimer(reply.secondstotal, reply.secondsremains);
}

var updateRound = onRoundReply;

var sendRoundAttempt = function() {
    var word = $("input[name=word]").val();
    $.getJSON($SCRIPT_ROOT + "/json/attempt", {'word': word}, onRoundReply);
    $("input[name=word]").val('');
    $("#error").addClass("invisible");
}

var drawCard = function(canvas, letter, score) {
    var fontFamily = "Calibri";
    var cardSize = Math.min(canvas.height, canvas.width);
    var margin = cardSize / 10;
    var letterFontSize = (cardSize * 65 / 100).toFixed();
    console.log(letterFontSize);
    var scoreFontSize = (cardSize * 30 / 100).toFixed();
    console.log(scoreFontSize);

    var ctx = canvas.getContext("2d");
    ctx.font = letterFontSize.toString() + "px " + fontFamily;
    ctx.textBaseline = "middle";
    var dim = ctx.measureText(letter);
    var x = (canvas.width - dim.width) / 2;
    var y = canvas.height / 2 - margin;
    ctx.fillText(letter, x, y);

    ctx.textBaseline = "alphabetic";
    ctx.font = scoreFontSize.toString() + "px " + fontFamily;
    score = score.toString();
    dim = ctx.measureText(score);
    x = (canvas.width - dim.width) / 2;
    y = canvas.height - margin;
    ctx.fillText(score, x, y);
};

var onWaitReply = function(reply) {
    if (reply.state != null && reply.state != 'waiting') {
        location.reload(true);
    }

    updateWaitingPlayers(reply.players);
}

var onChoosingReply = function(reply) {
    if (reply.state != null && reply.state != 'choosing') {
        location.reload(true);
    }
    updateTimer(reply.secondstotal, reply.secondsremains);
    if (reply.status === 'ok' && reply.chosenattempt && reply.chosenattempt.word) {
        $("tr.attempt").removeClass("success");
        $("tr.attempt td").filter(
                function() {
                    return $.trim($(this).text()) === reply.chosenattempt.word;
                }).parent().addClass("success");
    }
}

var updateWaitingPlayers = function(players) {
    $("#connected-players tr td").each(function(i, td) {
        if (i < players.length) {
            $(this).text(players[i]);
        } else {
            $(this).text('-');
        }
    });
};

var chooseWord = function(word) {
    $.getJSON($SCRIPT_ROOT + "/json/choose", {'word': word}, onChoosingReply);
}

var joinGame = function(gameId, successUrl) {
    var onJoinGameReply = function(reply) {
        if (reply.status === 'ok') {
            location.href = successUrl;
        }
    }
    $.getJSON($SCRIPT_ROOT + "/json/joingame", {'gameid': gameId}, onJoinGameReply);
}
