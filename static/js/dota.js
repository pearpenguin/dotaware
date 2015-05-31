var dota = (function() {
    var games = {};
    var leagues = {};
    
    function League(league) {
        this.name = this.sanitize_name(league.name);
        this.leagueid = league.leagueid;
        this.description = league.description;
        this.tournament_url = league.tournament_url;
        this.itemdef = league.itemdef;
    }
    //Remove tags from league name and convert underscore to spaces
    League.prototype.sanitize_name = function(name) {
        /*e.g. 
            "#DOTA_Item_joinDOTA_League_Season_3"
            "joinDOTA League Season 3"
        */
        name = name.replace("#DOTA_Item_", "");
        name = name.replace(/_/g, " ");
        return name;
    };
    
    function Game(game) {
        this.game = game; //Game structure
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
    Game.prototype.league_id = function() {
        try {
            return this.game.league_id;
        } catch (e){
            return undefined;
        }
    };
    Game.prototype.radiant_hero = function(slot) {
        try {
            return this.radiant_player(slot).hero_id;
        } catch (e){
            return undefined;
        }
    };
    Game.prototype.dire_hero = function(slot) {
        try {
            return this.dire_player(slot).hero_id;
        } catch (e){
            return undefined;
        }
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
            var id = this.game.scoreboard.radiant.players[slot].account_id;
            return this.game.players[id];
        } catch (e){
            return undefined;
        }
    };
    Game.prototype.dire_player = function(slot) {
        try {
            var id = this.game.scoreboard.dire.players[slot].account_id;
            return this.game.players[id];
        } catch (e){
            return undefined;
        }
    };
    Game.prototype.num_radiant_players = function() {
        try {
            return this.game.scoreboard.radiant.players.length;
        } catch (e){
            return 0;
        }
    };
    Game.prototype.num_dire_players = function() {
        try {
            return this.game.scoreboard.dire.players.length;
        } catch (e){
            return 0;
        }
    };
    //Return duration as float
    Game.prototype.duration = function() {
        try {
            return this.game.scoreboard.duration;
        } catch (e){
            return 0;
        }
    };
    //Display duration in mins and secs
    Game.prototype.duration_str = function() {
        var duration;
        try {
            duration = this.game.scoreboard.duration;
        } catch (e){
            return "0";
        }
        var mins = Math.floor(duration / 60);
        var secs = Math.floor(duration % 60);
        return mins + "m " + secs + "s";
    };
    Game.prototype.radiant_logo = function() {
        try {
            return this.game.radiant_team.logo_url;
        } catch (e){
            return undefined;
        }
    };
    Game.prototype.dire_logo = function() {
        try {
            return this.game.dire_team.logo_url;
        } catch (e){
            return undefined;
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
            return this.game.scoreboard.radiant.score;
        } catch (e){
            return undefined;
        }
    };
    Game.prototype.dire_score = function() {
        try {
            return this.game.scoreboard.dire.score;
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
        //Store newly active leagues
        update_leagues: function(new_leagues) {
            console.log("new leagues");
            console.log(new_leagues); //TODO: remove
            for (league_id in new_leagues) {
                leagues[league_id] = new League(new_leagues[league_id]);
            }
        },
        //TODO: garbage collect unused leagues
    };

    /* View functions */
    function v_simple_game_table(game) {

        //Return rows of players for the game table
        function v_player_rows() {
            //Number of rows is the team which has the most players
            var num_r = game.num_radiant_players();
            var num_d = game.num_dire_players();
            var max = num_r > num_d ? num_r : num_d;
            var rows = [], row;
            var cls_hero_img = ".dota-hero.dota-hero-"
            for (var i = 0; i < max; i++) {
                row = m("tr", [
                    m("td", game.radiant_player_name(i)),
                    m("td", [
                        m("div" + cls_hero_img + game.radiant_hero(i)),
                    ]),
                    m("td", [
                        m("div" + cls_hero_img + game.dire_hero(i)),
                    ]),
                    m("td", game.dire_player_name(i)),
                ]);
                rows.push(row);
            }
            return rows;
        }

        //Display team logos if available
        //TODO: scale logos properly
        var logo_url;
        var radiant = [game.radiant_name()];
        logo_url = game.radiant_logo();
        if (logo_url)
            radiant.push(m("img", {src: logo_url}));
        var dire = [game.dire_name()];
        logo_url = game.dire_logo();
        if (logo_url)
            dire.push(m("img", {src: logo_url}));
                
        return m("table", [
            //Team names and logos if available
            //Team names + scores
            m("tr", [
                m("td", radiant),
                m("td", game.radiant_score()),
                m("td", game.dire_score()),
                m("td", dire),
            ])
            //Players
        ].concat(v_player_rows()));
    }

    function v_simple_game(game) {
        var league = leagues[game.league_id()];
        var league_name = league ? league.name : "";
        return m("li", [
            //League name, duration of game
            m("div", league_name),
            m("div", game.duration_str()),
            //Team scores and players table
            v_simple_game_table(game),
        ]);
    }

    //Sort function for games by descending duration
    function sort_duration_desc(game1, game2) {
        //game1 comes first if it has higher duration
        var dur1 = game1.duration(), dur2 = game2.duration();
        if (dur1 > dur2)
            return -1;
        else if (dur2 > dur1)
            return 1;
        else
            return 0;
    }

    function view_games() {
        var matches = [];
        //Put games in a list and order them
        var ordering = []; 
        for (match_id in games) {
            ordering.push(games[match_id]);
        }
        //Sort by descending duration. TODO: offer other sort methods
        ordering.sort(sort_duration_desc);
        //Render the matches
        for (idx in ordering) {
            matches.push(v_simple_game(ordering[idx]));
        }
        return m("ul", matches)
    };

    return {
        vm: vm,
        controller: vm.init,
        games: games,
        leagues: leagues,
    };

})();
