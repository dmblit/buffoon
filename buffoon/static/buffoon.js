var updateBar = function() {
    var timebar = document.getElementById('timeremainsbar');
    if (timebar) {
        timebar.style.width = TIME_KEEPER.remainPercents().toString() + "%";
    }
}

var onRoundReply = function(reply) {
    if (reply.state != null && reply.state != 'round') {
        location.reload(true);
    }

    if (reply.millisecondstotal != null && reply.millisecondsremains != null) {
        TIME_KEEPER.refineTime(reply.millisecondstotal, reply.millisecondsremains);
    }
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
    TIME_KEEPER.refineTime(reply.secondstotal, reply.millisecondsremains);
}

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
    var scoreFontSize = (cardSize * 30 / 100).toFixed();

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
}

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
    TIME_KEEPER.refineTime(reply.millisecondstotal, reply.millisecondsremains);
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

var reload = function() {
    location.reload(true);
}

var TimeKeeper = function() {
    var that = this;
    that.endTime = Infinity;
    that.startTime = -Infinity;
    that.lastUpdate = null;
    that.nextUpdate = null;
    that.reloadId = null;
    that.refineIds = null;

    that.refineTime = function(millisecondstotal, millisecondsremains, now) {
        if (typeof now === "undefined") {
            now = new Date().getTime();
        }
        var endTimeGuess = now + millisecondsremains;
        if (that.endTime > endTimeGuess) {
            that.endTime = endTimeGuess;
            that.rescheduleReload(now);
            that.rescheduleRefine(now);
        }
        that.startTime = Math.max(that.startTime, that.endTime - millisecondstotal);
        that.lastUpdate = now;
    }

    that.rescheduleReload = function(now) {
        var newReload = window.setTimeout(function() {location.reload(true);}, that.endTime - now);
        if (that.reloadId !== null) {
            window.clearTimeout(that.reloadId);
        }
        that.reloadId = newReload;
    }

    that.rescheduleRefine = function(now) {
        if (that.refineIds === null) {
            var REFINE_COUNT = 3;
            var refineTimeout = (that.endTime - now)  / (REFINE_COUNT + 1);
            that.refineIds = [];
            for (var i = 0; i != REFINE_COUNT; ++i) {
                var tid = window.setTimeout(function() {
                    $.getJSON($SCRIPT_ROOT + "/json/getgamestate", function(reply) {
                        that.refineTime(reply.millisecondstotal, reply.millisecondsremains);
                    });
                }, refineTimeout * (1 + i));
                that.refineIds.push(tid);
            }
        }
    }

    that.remainPercents = function(now) {
        if (typeof now === "undefined") {
            now = new Date().getTime();
        }

        if (that.endTime === Infinity) {
            return 100;
        } else {
            return 100 * (that.endTime - now) / (that.endTime - that.startTime);
        }
    }
}

var StateUpdater = function() {
    var that = this;
    that.tick = function(now) {
        if (typeof now === "undefined") {
            now = new Date().getTime();
        }
    }
}
var TIME_KEEPER = new TimeKeeper();
