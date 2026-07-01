import Home from './Home.vue';

frappe.provide('frappe.PosApp');


frappe.PosApp.posapp = class {
    constructor({ parent }) {
        this.$parent = $(document);
        this.page = parent.page;
        this.make_body();

    }
    make_body () {
        this.$el = this.$parent.find('.main-section');
        this.vue = new Vue({
            vuetify: new Vuetify({
                rtl: frappe.utils.is_rtl(),
                theme: {
                    themes: {
                        light: {
                            background: '#F4F6FB',
                            surface: '#FFFFFF',
                            primary: '#17223B',
                            secondary: '#2CC8C2',
                            accent: '#5E60CE',
                            success: '#3BB273',
                            info: '#3A506B',
                            warning: '#F4A259',
                            error: '#EF476F',
                            muted: '#8A94A6',
                            badge: '#2CC8C2',
                            outline: '#E0E6F0',
                        },
                    },
                },
            }),
            el: this.$el[0],
            data: {
            },
            render: h => h(Home),
        });
    }
    setup_header () {

    }

};
