// Mobile menu toggle
document.addEventListener('DOMContentLoaded', function() {
    const menuButton = document.querySelector('.md\\:hidden');
    
    if (menuButton) {
        menuButton.addEventListener('click', function() {
            const nav = document.querySelector('.md\\:flex');
            nav.classList.toggle('hidden');
            nav.classList.toggle('flex');
            nav.classList.toggle('flex-col');
            nav.classList.toggle('absolute');
            nav.classList.toggle('top-16');
            nav.classList.toggle('right-0');
            nav.classList.toggle('bg-amber-800');
            nav.classList.toggle('p-4');
            nav.classList.toggle('rounded-b-lg');
            nav.classList.toggle('shadow-lg');
            nav.classList.toggle('w-full');
            nav.classList.toggle('space-y-4');
        });
    }
    
    let currentPage = location.pathname;
    
    document.addEventListener('click', function(e) {
        const link = e.target.closest('a');
        
        if (link && link.href && link.href.startsWith(window.location.origin) && !link.dataset.noTransition) {
            e.preventDefault();
            
            document.body.classList.add('page-exit');
            
            setTimeout(() => {
                window.location.href = link.href;
            }, 300);
        }
    });
    
    document.body.classList.add('page-enter');
    setTimeout(() => {
        document.body.classList.remove('page-enter');
    }, 500);
    
    window.addEventListener('popstate', function() {
        if (currentPage !== location.pathname) {
            document.body.classList.add('page-exit');
            setTimeout(() => {
                location.reload();
            }, 300);
        }
    });

    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', function(e) {
            const dropdown = this.querySelector('.dropdown-menu');
            if (dropdown && window.innerWidth < 768) {
                if (dropdown.classList.contains('hidden')) {
                    document.querySelectorAll('.dropdown-menu').forEach(menu => {
                        if (menu !== dropdown) {
                            menu.classList.add('hidden');
                        }
                    });
                    dropdown.classList.remove('hidden');
                } else {
                    dropdown.classList.add('hidden');
                }
                
                if (!e.target.closest('a') || e.target.nextElementSibling === dropdown) {
                    e.preventDefault();
                }
            }
        });
    });
    
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.nav-item') && window.innerWidth < 768) {
            document.querySelectorAll('.dropdown-menu').forEach(menu => {
                menu.classList.add('hidden');
            });
        }
    });
});