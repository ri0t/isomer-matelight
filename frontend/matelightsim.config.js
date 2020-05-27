import icon from './assets/iconmonstr-computer-3.svg';

export function routing($stateProvider) {

    $stateProvider
        .state('app.matelightsim', {
            url: '/matelightsim',
            template: '<matelightsim></matelightsim>',
            label: 'MatelightSim',
            icon: icon
        });
}
