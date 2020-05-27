import angular from 'angular';
import uirouter from 'angular-ui-router';

import {routing} from './matelightsim.config.js';

import './matelightsim/matelightsim.scss';

import matelightsimcomponent from './matelightsim/matelightsim.js';
import template from './matelightsim/matelightsim.tpl.html';

export default angular
    .module('main.app.matelightsim', [uirouter])
    .config(routing)
    .component('matelightsim', {controller: matelightsimcomponent, template: template})
    .name;
