var dota = (function() {
    var games = {}; //simple_game structure
    
    function update_simple_game(match_id, update) {
        var game = games[match_id];
        for (key in update) {
            game[key] = update[key];
        }
    }

    var vm = {
        init: function() {
        },
        update_gamelist: function(updates, new_games) {
            for (match_id in updates) {
                update_simple_game(match_id, updates[match_id]);
            }
            for (match_id in new_games) {
                games[match_id] = new_games[match_id];
            }
            console.log(games); //TODO: remove
            m.render(document.body, view());
        },
    };

    var view = function() {
        var matches = [];
        for (match_id in games) {
            matches.push(m("li", match_id));
        }
        return m("ul", matches)
    };

    return {
        vm: vm,
        controller: vm.init,
        view: view
    };

})();
