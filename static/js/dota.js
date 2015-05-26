var dota = (function() {
    var games = {};
    
    function Game(game) {
        this.game = game; //simple_game structure
        this.map_players(); //Map players on creation
    }
    //convert array of players into object with account_id as keys
    Game.prototype.map_players = function() {
        var players = {};
        var player;
        for (idx in this.game.players) {
            player = this.game.players[idx];
            players[player.account_id] = player;
        }
        this.game.players = players;
    };
    Game.prototype.radiant_player_name = function(slot) {
        try {
            return this.radiant_player(slot).name;
        } catch (e){
            return undefined;
        }
    };
    Game.prototype.dire_player_name = function(slot) {
        try {
            return this.dire_player(slot).name;
        } catch (e){
            return undefined;
        }
    };
    Game.prototype.radiant_player = function(slot) {
        try {
            return this.game.players[this.game.radiant.players[slot]];
        } catch (e){
            return undefined;
        }
    };
    Game.prototype.dire_player = function(slot) {
        try {
            return this.game.players[this.game.dire.players[slot]];
        } catch (e){
            return undefined;
        }
    };
    Game.prototype.num_radiant_players = function() {
        try {
            return this.game.radiant.players.length;
        } catch (e){
            return 0;
        }
    };
    Game.prototype.num_dire_players = function() {
        try {
            return this.game.dire.players.length;
        } catch (e){
            return 0;
        }
    };
    Game.prototype.duration = function() {
        try {
            return this.game.duration;
        } catch (e){
            return 0;
        }
    };
    Game.prototype.radiant_name = function() {
        try {
            return this.game.radiant_team.team_name;
        } catch (e){
            return undefined;
        }
    };
    Game.prototype.dire_name = function() {
        try {
            return this.game.dire_team.team_name;
        } catch (e){
            return undefined;
        }
    };
    Game.prototype.radiant_score = function() {
        try {
            return this.game.radiant.score;
        } catch (e){
            return undefined;
        }
    };
    Game.prototype.dire_score = function() {
        try {
            return this.game.dire.score;
        } catch (e){
            return undefined;
        }
    };

    Game.prototype.update = function(update) {
        for (key in update) {
            this.game[key] = update[key];
            //If new players received, convert to key-value
            if (key == 'players')
                this.map_players();
        }
    };

    var vm = {
        init: function() {
        },
        //Update the whole game list
        update_gamelist: function(updates, new_games) {
            //Store active games in new list to remove inactive games
            var active_games = {};
            //Get new games first, updates of the new games may follow
            for (match_id in new_games) {
                active_games[match_id] = new Game(new_games[match_id]);
            }
            //TODO: handle case of trying to update a missing game
            for (match_id in updates) {
                games[match_id].update(updates[match_id]);
                active_games[match_id] = games[match_id];
            }
            games = active_games;
            console.log(games); //TODO: remove
            m.render(document.body, view_games());
        },
    };

    /* View functions */
    function v_simple_game_table(game) {

        //Return rows of players for the game table
        function v_player_rows() {
            //Number of rows is the team which has the most players
            var num_r = game.num_radiant_players();
            var num_d = game.num_dire_players();
            var max = num_r > num_d ? num_r : num_d;
            var rows = [];
            var row, radiant_player, dire_player, r_name, d_name;
            for (var i = 0; i < max; i++) {
                row = m("tr", [
                    m("td", game.radiant_player_name(i)),
                    //TODO: radiant player hero
                    //TODO: dire player hero
                    m("td", game.dire_player_name(i)),
                ]);
                rows.push(row);
            }
            return rows;
        }

        return m("table", [
            //Team names + scores
            m("tr", [
                m("td", game.radiant_name()),
                m("td", game.radiant_score()),
                m("td", game.dire_score()),
                m("td", game.dire_name()),
            ])
            //Players
        ].concat(v_player_rows()));
    }

    function v_simple_game(match_id) {
        var game = games[match_id];
        return m("li", [
            //League name, duration of game
            //m("div", game.league_id),
            m("div", game.duration()),
            //Team scores and players table
            v_simple_game_table(game),
        ]);
    }

    function view_games() {
        var matches = [];
        for (match_id in games) {
            matches.push(v_simple_game(match_id));
        }
        return m("ul", matches)
    };

    return {
        vm: vm,
        controller: vm.init,
        games: games,
    };

})();
