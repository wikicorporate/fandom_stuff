const App = {
        template: AppTemplate,
        data: AppState.data,
        computed: AppState.computed,
        methods: Object.assign({}, AppMethodsApi, AppMethodsUi),
        
        mounted() { 
            this.fetchData(); 
        },
        beforeUnmount() {
            if (this.refreshInterval) {
                clearInterval(this.refreshInterval);
            }
            this.cleanUpRemoteResources();
        }
    };

    const targetContainer = document.querySelector('#cwa-app-container');
    if (targetContainer) { 
        document.body.classList.add('CrossWikiActivity');
        Vue.createMwApp(App).mount(targetContainer); 
    }
})();
