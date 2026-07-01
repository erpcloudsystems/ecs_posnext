import ItemManagerHome from './ItemManagerHome.vue';

frappe.provide('frappe.PosApp');

frappe.PosApp.ItemManagerApp = class {
    constructor({ parent }, item_id = null) {
        this.$parent = $(document);
        this.page = parent.page;
        this.item_id = item_id;
        this.make_body();
    }
    make_body() {
        this.$el = this.$parent.find('.main-section');
        const item_id = this.item_id;
        this.vue = new Vue({
            vuetify: new Vuetify({
                rtl: frappe.utils.is_rtl(),
                theme: {
                    themes: {
                        light: {
                            background: '#F4F6FB',
                            surface: '#FFFFFF',
                            primary: '#17223B',
                            secondary: '#FF9800',
                            accent: '#5E60CE',
                            success: '#3BB273',
                            info: '#3A506B',
                            warning: '#F4A259',
                            error: '#EF476F',
                            muted: '#8A94A6',
                            badge: '#FF9800',
                            outline: '#E0E6F0',
                        },
                    },
                },
            }),
            el: this.$el[0],
            data: {
                item_id: item_id
            },
            render: h => h(ItemManagerHome, { props: { itemId: item_id } }),
        });
    }
};
