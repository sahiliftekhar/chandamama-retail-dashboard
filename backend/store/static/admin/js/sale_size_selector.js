'use strict';

(function() {

    function ready(fn) {
        if (document.readyState !== 'loading') { fn(); }
        else { document.addEventListener('DOMContentLoaded', fn); }
    }

    function loadSizesForProduct(productId, currentSize) {
        if (!productId) return;
        var xhr = new XMLHttpRequest();
        xhr.open('GET', '/admin/api/product-sizes/?product_id=' + productId, true);
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4 && xhr.status === 200) {
                try {
                    var data = JSON.parse(xhr.responseText);
                    renderSizeSelect(data.sizes || [], currentSize);
                } catch(e) { console.log('Size load error:', e); }
            }
        };
        xhr.send();
    }

    function renderSizeSelect(sizes, currentSize) {
        var sizeField = document.getElementById('id_size');
        if (!sizeField) return;

        // ✅ Main size select — value is just the size (e.g. "NA")
        var select = document.createElement('select');
        select.id        = 'id_size';
        select.name      = 'size';
        select.className = sizeField.className || 'vTextField';

        var emptyOpt = document.createElement('option');
        emptyOpt.value       = '';
        emptyOpt.textContent = '— Select size —';
        select.appendChild(emptyOpt);

        sizes.forEach(function(item) {
            var opt = document.createElement('option');
            opt.value       = item.size;                  // ✅ just size, no pricing_id
            opt.dataset.pricingId = item.pricing_id;      // ✅ pricing_id stored in data attr
            opt.textContent = item.size + (item.marked_price ? ' — ₹' + item.marked_price : '');
            if (item.size === currentSize) { opt.selected = true; }
            select.appendChild(opt);
        });

        if (sizes.length === 1) {
            select.value = sizes[0].size;
        }

        sizeField.parentNode.replaceChild(select, sizeField);

        // ✅ Hidden pricing_id field
        var hiddenField = document.getElementById('id_pricing_id');
        if (!hiddenField) {
            hiddenField          = document.createElement('input');
            hiddenField.type     = 'hidden';
            hiddenField.id       = 'id_pricing_id';
            hiddenField.name     = 'pricing_id';
            select.parentNode.appendChild(hiddenField);
        }

        // ✅ Set initial pricing_id from selected option
        function syncPricingId() {
            var selected = select.options[select.selectedIndex];
            hiddenField.value = selected ? (selected.dataset.pricingId || '') : '';
        }

        syncPricingId();

        select.addEventListener('change', function() {
            syncPricingId();
            var selected = select.options[select.selectedIndex];
            var pricingId = selected ? (selected.dataset.pricingId || '') : '';
            updatePricingHint(select.value, pricingId, sizes);
        });

        if (select.value) {
            var selected  = select.options[select.selectedIndex];
            var pricingId = selected ? (selected.dataset.pricingId || '') : '';
            updatePricingHint(select.value, pricingId, sizes);
        }
    }

    function updatePricingHint(size, pricingId, sizes) {
        var old = document.getElementById('pricing-hint');
        if (old) old.remove();

        var pricing = pricingId
            ? sizes.find(function(s) { return String(s.pricing_id) === String(pricingId); })
            : sizes.find(function(s) { return s.size === size; });
        if (!pricing) return;

        var sellingField = document.getElementById('id_selling_price');
        if (sellingField && (!sellingField.value || sellingField.value === '0')) {
            sellingField.value = pricing.marked_price;
        }

        var hint = document.createElement('p');
        hint.id            = 'pricing-hint';
        hint.style.cssText = 'color:#fbbf24;font-size:11px;margin-top:4px;font-family:monospace';
        hint.textContent   = 'Purchase: ₹' + pricing.purchase_rate +
                             ' | Marked: ₹' + pricing.marked_price +
                             ' | Min (20% margin): ₹' + pricing.min_selling;
        if (sellingField) {
            sellingField.parentNode.insertBefore(hint, sellingField.nextSibling);
        }
    }

    ready(function() {
        var productField = document.getElementById('id_product');
        if (!productField) return;

        productField.addEventListener('change', function() {
            loadSizesForProduct(this.value, '');
        });

        if (productField.value) {
            var currentSize = document.getElementById('id_size') ?
                              document.getElementById('id_size').value : '';
            loadSizesForProduct(productField.value, currentSize);
        }
    });

})();