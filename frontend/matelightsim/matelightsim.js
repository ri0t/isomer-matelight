'use strict';

class matelightsimcomponent {

    constructor(socket, $state, $rootScope, user) {
        this.socket = socket;
        this.state = $state;
        this.rootscope = $rootScope;
        this.user = user;

        let self = this;

        this.rows = [];

        for (let i=0; i <16; i++) {
            let col = [];
            for (let j=0; j <40; j++) {
                col.push([255, 0, 0]);
            }
            this.rows.push(col)
        }

        console.log('[MLSIM] Initializing');

        this.subscribe = function() {
            console.log('[MLSIM] Subscribing');

            self.socket.send({
                component: 'isomer.matelightsim',
                action: 'subscribe',
            });
        };

        this.update = function(msg) {
            self.rows = msg.data;
        }

        if (this.user.signed_in) {
            console.log("[MLSIM] Logged in, subscribing")
            this.subscribe();
        }
        this.loginupdate = this.rootscope.$on('User.Login', self.subscribe);
        this.socketupdate = this.socket.listen('isomer.matelightsim', self.update)

    }

    getElementStyle(col) {
        return {background: "rgb(" + col[0] + ", " + col[1] + ", " + col[2] + ")"}
    }
}

matelightsimcomponent.$inject = ['socket', '$state', '$rootScope', 'user'];

export default matelightsimcomponent;
