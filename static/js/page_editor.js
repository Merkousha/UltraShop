/**
 * Page editor: Sortable drag-and-drop and publish confirm.
 * Loaded from dashboard/page_editor.html; no inline scripts (CSP-safe).
 */
(function() {
    var list = document.getElementById('block-list');
    var input = document.getElementById('block_order');
    if (list && input && typeof Sortable !== 'undefined') {
        new Sortable(list, {
            animation: 150,
            handle: '.cursor-grab',
            onEnd: function() {
                var ids = [];
                list.querySelectorAll('[data-block-id]').forEach(function(el) {
                    ids.push(el.getAttribute('data-block-id'));
                });
                input.value = ids.join(',');
            }
        });
    }

    var publishForm = document.getElementById('publish-form');
    if (publishForm) {
        publishForm.addEventListener('submit', function(e) {
            if (!confirm('آیا می\u200cخواهید این چیدمان روی فروشگاه منتشر شود؟')) {
                e.preventDefault();
            }
        });
    }

    document.querySelectorAll('.block-settings-toggle').forEach(function(btn) {
        btn.addEventListener('click', function() {
            var id = this.getAttribute('data-block-id');
            var panel = document.getElementById('settings-' + id);
            if (!panel) return;
            var isHidden = panel.classList.toggle('hidden');
            btn.setAttribute('aria-expanded', isHidden ? 'false' : 'true');
        });
    });

    var removeForm = document.getElementById('remove-block-form');
    var removeBlockIdInput = document.getElementById('remove-block-id');
    document.querySelectorAll('.remove-block-btn').forEach(function(btn) {
        btn.addEventListener('click', function() {
            if (!removeForm || !removeBlockIdInput) {
                return;
            }
            if (!confirm('این بلوک حذف شود؟')) {
                return;
            }
            removeBlockIdInput.value = btn.getAttribute('data-block-id') || '';
            removeForm.submit();
        });
    });
})();
