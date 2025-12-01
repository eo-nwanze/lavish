// Mobile Sidebar Functions
function toggleMobileSidebar() {
  const burgerIcon = document.querySelector('.burger-icon');
  const mobileSidebar = document.querySelector('.account-sidebar.mobile');
  const overlay = document.querySelector('.mobile-sidebar-overlay');
  
  burgerIcon.classList.toggle('active');
  mobileSidebar.classList.toggle('active');
  overlay.classList.toggle('active');
  
  // Prevent body scroll when sidebar is open
  document.body.style.overflow = mobileSidebar.classList.contains('active') ? 'hidden' : '';
}

function closeMobileSidebar() {
  const burgerIcon = document.querySelector('.burger-icon');
  const mobileSidebar = document.querySelector('.account-sidebar.mobile');
  const overlay = document.querySelector('.mobile-sidebar-overlay');
  
  burgerIcon.classList.remove('active');
  mobileSidebar.classList.remove('active');
  overlay.classList.remove('active');
  document.body.style.overflow = '';
}

// Close sidebar when clicking outside or pressing escape
document.addEventListener('click', function(e) {
  const mobileSidebar = document.querySelector('.account-sidebar.mobile');
  const overlay = document.querySelector('.mobile-sidebar-overlay');
  
  if (mobileSidebar.classList.contains('active') && !mobileSidebar.contains(e.target) && !e.target.closest('.burger-icon')) {
    closeMobileSidebar();
  }
});

document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') {
    closeMobileSidebar();
  }
});

// Tab Navigation
function showTab(tabId) {
  const navLinks = document.querySelectorAll('.nav-link');
  const tabContents = document.querySelectorAll('.tab-content');
  
  // Remove active class from all links and tabs
  navLinks.forEach(l => l.classList.remove('active'));
  tabContents.forEach(t => t.classList.remove('active'));
  
  // Add active class to target links and tab
  const targetLinks = document.querySelectorAll(`[data-tab="${tabId}"]`);
  const targetTab = document.getElementById(tabId);
  
  if (targetLinks.length > 0 && targetTab) {
    targetLinks.forEach(link => link.classList.add('active'));
    targetTab.classList.add('active');
  }
  
  // Save active tab to localStorage
  localStorage.setItem('activeAccountTab', tabId);
}

// Orders Tab Navigation Functions
function showOrderSubtab(subtabName) {
  // Remove active class from all subtabs
  document.querySelectorAll('.order-subtab').forEach(tab => {
    tab.classList.remove('active');
  });
  
  // Hide all subtab content
  document.querySelectorAll('.order-subtab-content').forEach(content => {
    content.classList.remove('active');
    content.style.display = 'none';
  });
  
  // Add active class to clicked subtab
  const clickedTab = event ? event.target : document.querySelector(`[onclick*="${subtabName}"]`);
  if (clickedTab) {
    clickedTab.classList.add('active');
  }
  
  // Show corresponding content
  const content = document.getElementById(subtabName + '-orders');
  if (content) {
    content.classList.add('active');
    content.style.display = 'block';
  }
  
  // Sync mobile dropdown
  const mobileDropdown = document.getElementById('mobile-order-tab-select');
  if (mobileDropdown) {
    mobileDropdown.value = subtabName;
  }
}

// Mobile dropdown handler for orders tab
function handleMobileOrderDropdown() {
  const dropdown = document.getElementById('mobile-order-tab-select');
  if (dropdown) {
    dropdown.addEventListener('change', function() {
      showOrderSubtab(this.value);
    });
  }
}

// Action Dropdown Functions
function toggleActionDropdown(menuId) {
  // Close all other dropdowns
  document.querySelectorAll('.action-menu').forEach(menu => {
    if (menu.id !== menuId) {
      menu.classList.remove('show');
    }
  });
  
  // Toggle current dropdown
  const dropdown = document.getElementById(menuId);
  if (dropdown) {
    dropdown.classList.toggle('show');
  }
}

// Close dropdowns when clicking outside
document.addEventListener('click', function(e) {
  if (!e.target.closest('.action-dropdown')) {
    document.querySelectorAll('.action-menu').forEach(menu => {
      menu.classList.remove('show');
    });
  }
});

// Search and Filter Functions
function initializeOrderSearch() {
  const searchInput = document.getElementById('orderSearch');
  const statusFilter = document.getElementById('statusFilter');
  const fulfillmentFilter = document.getElementById('fulfillmentFilter');
  const tableBody = document.getElementById('ordersTableBody');
  
  if (!searchInput || !tableBody) return;
  
  function filterTable() {
    const searchTerm = searchInput.value.toLowerCase();
    const statusValue = statusFilter.value.toLowerCase();
    const fulfillmentValue = fulfillmentFilter.value.toLowerCase();
    const rows = tableBody.querySelectorAll('.order-row');
    
    rows.forEach(row => {
      if (window.innerWidth > 768) {
        const orderId = row.querySelector('.order-link')?.textContent.toLowerCase() || '';
        const date = row.querySelector('.order-date')?.textContent.toLowerCase() || '';
        const items = row.querySelector('.order-items')?.textContent.toLowerCase() || '';
        const status = row.querySelector('.status-badge')?.textContent.toLowerCase() || '';
        const fulfillment = row.querySelectorAll('.status-badge')[1]?.textContent.toLowerCase() || '';
        
        const matchesSearch = orderId.includes(searchTerm) || 
                             date.includes(searchTerm) || 
                             items.includes(searchTerm);
        const matchesStatus = !statusValue || status.includes(statusValue);
        const matchesFulfillment = !fulfillmentValue || fulfillment.includes(fulfillmentValue);
        
        if (matchesSearch && matchesStatus && matchesFulfillment) {
          row.style.display = '';
        } else {
          row.style.display = 'none';
        }
      } else {
        // Mobile filtering logic
        const mobileHeader = document.createElement('div');
        mobileHeader.classList.add('order-row-mobile-header');
        
        const orderLink = row.querySelector('.order-link').cloneNode(true);
        const actionDropdown = row.querySelector('.action-dropdown').cloneNode(true);
        
        mobileHeader.appendChild(orderLink);
        mobileHeader.appendChild(actionDropdown);
        
        // Remove existing header if it exists
        const existingHeader = row.querySelector('.order-row-mobile-header');
        if (existingHeader) {
          existingHeader.remove();
        }
        
        row.insertBefore(mobileHeader, row.firstChild);
        
        // Hide original elements
        row.querySelector('td[data-label="Order"]').style.display = 'none';
        row.querySelector('.actions-cell').style.display = 'none';
        
        const rowText = row.textContent.toLowerCase();
        if (rowText.includes(searchTerm)) {
          row.style.display = 'block';
        } else {
          row.style.display = 'none';
        }
      }
    });
    
    // Show/hide empty state
    const visibleRows = Array.from(rows).filter(row => row.style.display !== 'none');
    const emptyState = tableBody.nextElementSibling;
    if (emptyState && emptyState.classList.contains('empty-state')) {
      emptyState.style.display = visibleRows.length === 0 ? 'block' : 'none';
    }
  }
  
  searchInput.addEventListener('input', filterTable);
  statusFilter.addEventListener('change', filterTable);
  fulfillmentFilter.addEventListener('change', filterTable);
  
  // Initial setup for mobile view
  if (window.innerWidth <= 768) {
    const rows = tableBody.querySelectorAll('.order-row');
    rows.forEach(row => {
      const mobileHeader = document.createElement('div');
      mobileHeader.classList.add('order-row-mobile-header');
      
      const orderLink = row.querySelector('.order-link').cloneNode(true);
      const actionDropdown = row.querySelector('.action-dropdown').cloneNode(true);
      
      mobileHeader.appendChild(orderLink);
      mobileHeader.appendChild(actionDropdown);
      
      row.insertBefore(mobileHeader, row.firstChild);
      
      // Hide original elements
      row.querySelector('td[data-label="Order"]').style.display = 'none';
      row.querySelector('.actions-cell').style.display = 'none';
    });
  }
}

// Initialize search when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
  initializeOrderSearch();
  
  // Initialize tab persistence
  const savedTab = localStorage.getItem('activeAccountTab');
  if (savedTab) {
    showTab(savedTab);
  }

  const navLinks = document.querySelectorAll('.nav-link');
  navLinks.forEach(link => {
    link.addEventListener('click', function(e) {
      e.preventDefault();
      const tabId = this.getAttribute('data-tab');
      showTab(tabId);
    });
  });
  
  // Initialize mobile dropdown handler
  handleMobileOrderDropdown();
});

// Notification System
function showNotification(message, type = 'success', duration = 4000) {
  const container = document.getElementById('notification-container');
  if (!container) {
    // Create notification container if it doesn't exist
    const notificationContainer = document.createElement('div');
    notificationContainer.id = 'notification-container';
    notificationContainer.style.cssText = `
      position: fixed;
      top: 2rem;
      right: 2rem;
      z-index: 9999;
      pointer-events: none;
    `;
    document.body.appendChild(notificationContainer);
  }
  
  const notification = document.createElement('div');
  const bgColor = type === 'success' ? '#28a745' : type === 'error' ? '#dc3545' : type === 'warning' ? '#ffc107' : '#17a2b8';
  const textColor = type === 'warning' ? '#000' : '#fff';
  
  notification.innerHTML = `
    <div style="
      background-color: ${bgColor}; 
      color: ${textColor}; 
      padding: 1rem 1.5rem; 
      border-radius: 0.5rem; 
      margin-bottom: 1rem; 
      box-shadow: 0 0.4rem 0.8rem rgba(0,0,0,0.15);
      transform: translateX(100%);
      transition: transform 0.3s ease;
      font-size: 1.3rem;
      font-weight: 500;
      position: relative;
      cursor: pointer;
      pointer-events: auto;
    " onclick="this.parentElement.remove()">
      ${message}
      <div style="position: absolute; top: 0.5rem; right: 1rem; font-size: 1.6rem; opacity: 0.8;">&times;</div>
    </div>
  `;
  
  container.appendChild(notification);
  
  // Animate in
  setTimeout(() => {
    notification.firstElementChild.style.transform = 'translateX(0)';
  }, 100);
  
  // Auto remove
  setTimeout(() => {
    if (notification.parentElement) {
      notification.firstElementChild.style.transform = 'translateX(100%)';
      setTimeout(() => {
        if (notification.parentElement) {
          notification.remove();
        }
      }, 300);
    }
  }, duration);
}

// Order Management Functions
function viewOrderDetails(orderId) {
  const modal = document.getElementById('order-details-modal');
  if (modal) {
    modal.classList.add('active');
  }
}

function closeOrderDetailsModal() {
  const modal = document.getElementById('order-details-modal');
  if (modal) {
    modal.classList.remove('active');
  }
}

function editOrder(orderId) {
  const modal = document.getElementById('edit-order-modal');
  if (modal) {
    modal.classList.add('active');
    // In a real implementation, you would fetch order data and populate the form
    showNotification('✏️ Loading order details...', 'info');
  }
}

function trackOrder(orderId) {
  const modal = document.getElementById('track-order-modal');
  if (modal) {
    modal.classList.add('active');
    // In a real implementation, you would fetch tracking data
    showNotification('📦 Loading tracking information...', 'info');
  }
}

function downloadInvoice(orderId) {
  // Create a sample invoice download
  const invoiceData = {
    orderId: orderId,
    date: new Date().toLocaleDateString(),
    total: '£37.90',
    items: [
      { name: 'Fantasy Romance Collection', price: '£29.90' },
      { name: 'Exclusive Bookmark', price: '£5.00' },
      { name: 'Reading Guide', price: '£3.00' }
    ]
  };
  
  // Create a simple text invoice
  const invoiceText = `
LAVISH LIBRARY - INVOICE
========================
Order #: ${orderId}
Date: ${invoiceData.date}
------------------------
ITEMS:
${invoiceData.items.map(item => `${item.name}: ${item.price}`).join('\n')}
------------------------
Subtotal: ${invoiceData.total}
Tax: £3.79
Total: £41.69
------------------------
Thank you for your order!
  `.trim();
  
  // Create and download the file
  const blob = new Blob([invoiceText], { type: 'text/plain' });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `invoice-${orderId}.txt`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  window.URL.revokeObjectURL(url);
  
  showNotification('📄 Invoice downloaded successfully!', 'success');
}

function cancelOrder(orderId) {
  if (confirm('Are you sure you want to cancel this order?')) {
    showNotification('❌ Order cancelled successfully', 'success');
    // Implementation would go here
  }
}

function reorderItems(orderId) {
  const modal = document.getElementById('reorder-modal');
  if (modal) {
    modal.classList.add('active');
    // In a real implementation, you would fetch the order items
    showNotification('🔄 Loading previous order items...', 'info');
  }
}

function writeReview(orderId) {
  const modal = document.getElementById('write-review-modal');
  if (modal) {
    modal.classList.add('active');
    // Reset form
    document.getElementById('review-title').value = '';
    document.getElementById('review-content').value = '';
    document.getElementById('recommend-product').checked = false;
    // Reset stars
    document.querySelectorAll('.star').forEach(star => {
      star.style.color = '#ddd';
    });
    showNotification('⭐ Opening review form...', 'info');
  }
}

function editUpcomingOrder(orderId) {
  const modal = document.getElementById('edit-order-modal');
  if (modal) {
    modal.classList.add('active');
  }
}

function closeEditOrderModal() {
  const modal = document.getElementById('edit-order-modal');
  if (modal) {
    modal.classList.remove('active');
  }
}

function skipUpcomingOrder(orderId) {
  const modal = document.getElementById('skip-payment-modal');
  if (modal) {
    modal.classList.add('active');
  }
}

function cancelUpcomingOrder(orderId) {
  const modal = document.getElementById('cancel-order-modal');
  if (modal) {
    modal.classList.add('active');
  }
}

function closeCancelOrderModal() {
  const modal = document.getElementById('cancel-order-modal');
  if (modal) {
    modal.classList.remove('active');
  }
}

function confirmCancelOrder() {
  showNotification('❌ Order cancelled successfully', 'success');
  closeCancelOrderModal();
}

function removeItem(itemId) {
  showNotification('✕ Item removed from order', 'success');
}

// Subscription Modal Functions
function skipNextPayment(subscriptionId) {
  const modal = document.getElementById('skip-payment-modal');
  modal.classList.add('active');
}

function closeSkipPaymentModal() {
  document.getElementById('skip-payment-modal').classList.remove('active');
}

function changeAddress(subscriptionId) {
  const modal = document.getElementById('change-address-modal');
  if (modal) {
    modal.classList.add('active');
    // Load countries, states, and country codes for the change address modal
    loadCountriesForChangeAddress();
  }
}

function changePayment(subscriptionId) {
  const modal = document.getElementById('change-payment-modal');
  modal.classList.add('active');
}

function closeChangePaymentModal() {
  document.getElementById('change-payment-modal').classList.remove('active');
}

function cancelSubscription(subscriptionId) {
  const modal = document.getElementById('cancel-subscription-modal');
  modal.classList.add('active');
}

function closeCancelSubscriptionModal() {
  document.getElementById('cancel-subscription-modal').classList.remove('active');
}

function viewSubscriptionHistory(subscriptionId) {
  // Navigate to Orders tab and show Cancelled Orders subtab
  showTab('orders');
  
  // Switch to cancelled orders subtab
  setTimeout(() => {
    // Use the existing showOrderSubtab function
    showOrderSubtab('cancelled-orders');
  }, 100);
  
  // Show notification
  showNotification(`📋 Navigating to cancelled orders for subscription ${subscriptionId}...`, 'info');
}

// Address Modal Functions
function openAddressWizard() {
  document.getElementById('address-modal').classList.add('active');
  loadCountries();
}

function closeAddressModal() {
  document.getElementById('address-modal').classList.remove('active');
  document.getElementById('address-form').reset();
}

function editAddress(addressId) {
  document.getElementById('edit-address-modal').classList.add('active');
  loadEditCountries();
  // In a real implementation, you would fetch the address data and populate the form
}

function closeEditAddressModal() {
  document.getElementById('edit-address-modal').classList.remove('active');
  document.getElementById('edit-address-form').reset();
}

// Payment Method Modal Functions
function openPaymentModal(mode, paymentId = null) {
  const modal = document.getElementById('payment-modal');
  const title = document.getElementById('payment-modal-title');
  
  if (mode === 'edit') {
    title.textContent = '✏️ Edit Payment Method';
    // In a real implementation, you would fetch and populate the payment method data
  } else {
    title.textContent = '💳 Add Payment Method';
    document.getElementById('payment-form').reset();
  }
  
  modal.classList.add('active');
}

function closePaymentModal() {
  document.getElementById('payment-modal').classList.remove('active');
}

// Confirmation Modal Functions
function showConfirmationModal({ title, message, icon, warningMessage, confirmText, onConfirm }) {
  const modal = document.getElementById('confirmation-modal');
  document.getElementById('confirmation-title').textContent = title;
  document.getElementById('confirmation-message').textContent = message;
  document.getElementById('confirmation-icon').textContent = icon;
  document.getElementById('confirmation-button').textContent = confirmText;
  
  const warning = document.getElementById('confirmation-warning');
  if (warningMessage) {
    document.getElementById('confirmation-warning-message').textContent = warningMessage;
    warning.style.display = 'block';
  } else {
    warning.style.display = 'none';
  }

  document.getElementById('confirmation-button').onclick = onConfirm;
  modal.classList.add('active');
}

function closeConfirmationModal() {
  document.getElementById('confirmation-modal').classList.remove('active');
}

function setDefaultAddress(addressId) {
  showConfirmationModal({
    title: '⭐ Set as Default Address?',
    message: 'Are you sure you want to set this address as your default?',
    icon: '⭐',
    confirmText: 'Set as Default',
    onConfirm: () => confirmSetDefaultAddress(addressId)
  });
}

function confirmSetDefaultAddress(addressId) {
  showNotification('✅ Address set as default!', 'success');
  closeConfirmationModal();
}

function setDefaultPayment(paymentId) {
  showConfirmationModal({
    title: '⭐ Set as Default?',
    message: 'Are you sure you want to set this payment method as your default?',
    icon: '⭐',
    confirmText: 'Set as Default',
    onConfirm: () => confirmSetDefault(paymentId)
  });
}

function confirmSetDefault(paymentId) {
  showNotification('✅ Payment method set as default!', 'success');
  closeConfirmationModal();
}

function showDeleteModal(type, id, name) {
  showConfirmationModal({
    title: `🗑️ Delete ${type === 'address' ? 'Address' : 'Payment Method'}?`,
    message: `Are you sure you want to delete "${name}"?`,
    icon: '🗑️',
    warningMessage: 'This action is permanent and cannot be reversed.',
    confirmText: 'Delete Permanently',
    onConfirm: () => confirmDelete(type, id, name)
  });
}

function confirmDelete(type, id, name) {
  showNotification(`✅ ${type === 'address' ? 'Address' : 'Payment method'} "${name}" has been deleted successfully!`, 'success');
  
  if (window.djangoIntegration) {
    const endpoint = type === 'address' ? '/customers/addresses/delete/' : '/customers/payment-methods/delete/';
    window.djangoIntegration.makeRequest(endpoint, 'DELETE', {
      customer_id: customerId,
      item_id: id
    });
  }
  
  closeConfirmationModal();
  
  setTimeout(() => {
    location.reload();
  }, 1500);
}

document.addEventListener('DOMContentLoaded', function() {
  const navLinks = document.querySelectorAll('.nav-link');
  navLinks.forEach(link => {
    link.addEventListener('click', function(e) {
      e.preventDefault();
      const tabId = this.getAttribute('data-tab');
      showTab(tabId);
    });
  });

  // Load country codes for personal info tab
  loadCountryCodesForPersonalInfo();
});

// Modal Functions for Order Actions
function closeEditOrderModal() {
  const modal = document.getElementById('edit-order-modal');
  if (modal) {
    modal.classList.remove('active');
  }
}

function closeTrackOrderModal() {
  const modal = document.getElementById('track-order-modal');
  if (modal) {
    modal.classList.remove('active');
  }
}

function closeWriteReviewModal() {
  const modal = document.getElementById('write-review-modal');
  if (modal) {
    modal.classList.remove('active');
  }
}

function closeReorderModal() {
  const modal = document.getElementById('reorder-modal');
  if (modal) {
    modal.classList.remove('active');
  }
}

function saveOrderChanges() {
  showNotification('✅ Order changes saved successfully!', 'success');
  closeEditOrderModal();
  // In a real implementation, you would send the data to the backend
}

function copyTrackingNumber() {
  const trackingNumber = 'UK1234567890';
  navigator.clipboard.writeText(trackingNumber).then(() => {
    showNotification('📋 Tracking number copied to clipboard!', 'success');
  }).catch(() => {
    showNotification('❌ Failed to copy tracking number', 'error');
  });
}

function setRating(rating) {
  const stars = document.querySelectorAll('.star');
  stars.forEach((star, index) => {
    if (index < rating) {
      star.style.color = '#FFD700';
    } else {
      star.style.color = '#ddd';
    }
  });
}

function submitReview() {
  const title = document.getElementById('review-title').value;
  const content = document.getElementById('review-content').value;
  const recommend = document.getElementById('recommend-product').checked;
  
  if (!title || !content) {
    showNotification('⚠️ Please fill in all required fields', 'warning');
    return;
  }
  
  showNotification('⭐ Review submitted successfully!', 'success');
  closeWriteReviewModal();
  // In a real implementation, you would send the review to the backend
}

function addToCart() {
  showNotification('🛒 Items added to cart successfully!', 'success');
  closeReorderModal();
  // In a real implementation, you would add the items to the Shopify cart
  setTimeout(() => {
    window.location.href = '/cart';
  }, 1500);
}

function loadCountryCodesForPersonalInfo() {
  const countryCodeSelect = document.getElementById('phone_country_code');
  if (!countryCodeSelect) return;

  // Fetch countries from API
  fetch(`${getApiBaseUrl()}/locations/countries/`)
    .then(response => {
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      return response.json();
    })
    .then(data => {
      countryCodeSelect.innerHTML = '<option value="">Select...</option>';
      data.forEach(country => {
        const option = document.createElement('option');
        option.value = `+${country.phone_code}`;
        option.textContent = `${country.name} (+${country.phone_code})`;
        countryCodeSelect.appendChild(option);
      });
    })
    .catch(error => {
      console.error('Error fetching countries for phone codes:', error);
      countryCodeSelect.innerHTML = '<option value="">Error loading countries</option>';
    });
}

// Change Address Modal Functions
function closeChangeAddressModal() {
  const modal = document.getElementById('change-address-modal');
  if (modal) {
    modal.classList.remove('active');
    document.getElementById('change-address-form').reset();
  }
}

function getApiBaseUrl() {
  if (window.location.hostname === 'localhost') {
    return 'http://127.0.0.1:8003/api'; // Development
  } else {
    return 'https://lavish-backend.endevops.net/api'; // Production (includes myshopify.com)
  }
}

function loadCountries() {
  const countrySelect = document.getElementById('addr_country');
  const countryCodeSelect = document.getElementById('addr_country_code');

  fetch(`${getApiBaseUrl()}/locations/countries/`)
    .then(response => {
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      return response.json();
    })
    .then(data => {
      countrySelect.innerHTML = '<option value="">Select a country...</option>';
      countryCodeSelect.innerHTML = '<option value="">Select...</option>';
      data.forEach(country => {
        const option = document.createElement('option');
        option.value = country.id;
        option.textContent = country.name;
        countrySelect.appendChild(option);

        const codeOption = document.createElement('option');
        codeOption.value = `+${country.phone_code}`;
        codeOption.textContent = `(+${country.phone_code})`;
        countryCodeSelect.appendChild(codeOption);
      });
      countrySelect.addEventListener('change', () => {
        loadStates(countrySelect.value);
        const selectedCountry = data.find(c => c.id == countrySelect.value);
        if (selectedCountry) {
          countryCodeSelect.value = `+${selectedCountry.phone_code}`;
          document.getElementById('addr_phone').value = '';
        }
      });
    })
    .catch(error => {
      console.error('Error fetching countries:', error);
      countrySelect.innerHTML = '<option value="">Error loading countries</option>';
    });
}

function loadStates(countryId) {
  const stateSelect = document.getElementById('addr_province');
  const citySelect = document.getElementById('addr_city');

  fetch(`${getApiBaseUrl()}/locations/countries/${countryId}/states/`)
    .then(response => {
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      return response.json();
    })
    .then(data => {
      stateSelect.innerHTML = '<option value="">Select state/province...</option>';
      citySelect.innerHTML = '<option value="">Select state first...</option>';
      if (data.length > 0) {
        data.forEach(state => {
          const option = document.createElement('option');
          option.value = state.id;
          option.textContent = state.name;
          stateSelect.appendChild(option);
        });
        stateSelect.addEventListener('change', () => loadCities(stateSelect.value));
      } else {
        stateSelect.innerHTML = '<option value="N/A">N/A</option>';
        citySelect.innerHTML = '<option value="">Enter city manually...</option>';
      }
    })
    .catch(error => {
      console.error('Error fetching states:', error);
      stateSelect.innerHTML = '<option value="">Error loading states</option>';
    });
}

function loadCities(stateId) {
  const citySelect = document.getElementById('addr_city');

  fetch(`${getApiBaseUrl()}/locations/states/${stateId}/cities/`)
    .then(response => {
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      return response.json();
    })
    .then(data => {
      citySelect.innerHTML = '<option value="">Select a city...</option>';
      if (data.length > 0) {
        data.forEach(city => {
          const option = document.createElement('option');
          option.value = city.id;
          option.textContent = city.name;
          citySelect.appendChild(option);
        });
      } else {
        citySelect.innerHTML = '<option value="">Enter city manually...</option>';
      }
    })
    .catch(error => {
      console.error('Error fetching cities:', error);
      citySelect.innerHTML = '<option value="">Error loading cities</option>';
    });
}

function loadEditCountries() {
  const countrySelect = document.getElementById('edit_addr_country');
  const countryCodeSelect = document.getElementById('edit_addr_country_code');

  fetch(`${getApiBaseUrl()}/locations/countries/`)
    .then(response => {
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      return response.json();
    })
    .then(data => {
      countrySelect.innerHTML = '<option value="">Select a country...</option>';
      countryCodeSelect.innerHTML = '<option value="">Select...</option>';
      data.forEach(country => {
        const option = document.createElement('option');
        option.value = country.id;
        option.textContent = country.name;
        countrySelect.appendChild(option);

        const codeOption = document.createElement('option');
        codeOption.value = `+${country.phone_code}`;
        codeOption.textContent = `(+${country.phone_code})`;
        countryCodeSelect.appendChild(codeOption);
      });
      countrySelect.addEventListener('change', () => {
        loadEditStates(countrySelect.value);
        const selectedCountry = data.find(c => c.id == countrySelect.value);
        if (selectedCountry) {
          countryCodeSelect.value = `+${selectedCountry.phone_code}`;
          document.getElementById('edit_addr_phone').value = '';
        }
      });
    })
    .catch(error => {
      console.error('Error fetching countries:', error);
      countrySelect.innerHTML = '<option value="">Error loading countries</option>';
    });
}

function loadEditStates(countryId) {
  const stateSelect = document.getElementById('edit_addr_province');
  const citySelect = document.getElementById('edit_addr_city');

  fetch(`${getApiBaseUrl()}/locations/countries/${countryId}/states/`)
    .then(response => {
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      return response.json();
    })
    .then(data => {
      stateSelect.innerHTML = '<option value="">Select state/province...</option>';
      citySelect.innerHTML = '<option value="">Select state first...</option>';
      if (data.length > 0) {
        data.forEach(state => {
          const option = document.createElement('option');
          option.value = state.id;
          option.textContent = state.name;
          stateSelect.appendChild(option);
        });
        stateSelect.addEventListener('change', () => loadEditCities(stateSelect.value));
      } else {
        stateSelect.innerHTML = '<option value="N/A">N/A</option>';
        citySelect.innerHTML = '<option value="">Enter city manually...</option>';
      }
    })
    .catch(error => {
      console.error('Error fetching states:', error);
      stateSelect.innerHTML = '<option value="">Error loading states</option>';
    });
}

function loadEditCities(stateId) {
  const citySelect = document.getElementById('edit_addr_city');

  fetch(`${getApiBaseUrl()}/locations/states/${stateId}/cities/`)
    .then(response => {
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      return response.json();
    })
    .then(data => {
      citySelect.innerHTML = '<option value="">Select a city...</option>';
      if (data.length > 0) {
        data.forEach(city => {
          const option = document.createElement('option');
          option.value = city.id;
          option.textContent = city.name;
          citySelect.appendChild(option);
        });
      } else {
        citySelect.innerHTML = '<option value="">Enter city manually...</option>';
      }
    })
    .catch(error => {
      console.error('Error fetching cities:', error);
      citySelect.innerHTML = '<option value="">Error loading cities</option>';
    });
}

function loadCountriesForChangeAddress() {
  const countrySelect = document.getElementById('change_addr_country');
  const countryCodeSelect = document.getElementById('change_addr_country_code');

  fetch(`${getApiBaseUrl()}/locations/countries/`)
    .then(response => response.json())
    .then(data => {
      countrySelect.innerHTML = '<option value="">Select a country...</option>';
      countryCodeSelect.innerHTML = '<option value="">Select...</option>';
      data.forEach(country => {
        const option = document.createElement('option');
        option.value = country.id;
        option.textContent = country.name;
        countrySelect.appendChild(option);

        const codeOption = document.createElement('option');
        codeOption.value = `+${country.phone_code}`;
        codeOption.textContent = `(+${country.phone_code})`;
        countryCodeSelect.appendChild(codeOption);
      });
      countrySelect.addEventListener('change', () => {
        loadStatesForChangeAddress(countrySelect.value);
        const selectedCountry = data.find(c => c.id == countrySelect.value);
        if (selectedCountry) {
          countryCodeSelect.value = `+${selectedCountry.phone_code}`;
          document.getElementById('change_addr_phone').value = '';
        }
      });
    })
    .catch(error => {
      console.error('Error fetching countries:', error);
      countrySelect.innerHTML = '<option value="">Error loading countries</option>';
    });
}

function loadStatesForChangeAddress(countryId) {
  const stateSelect = document.getElementById('change_addr_province');
  const citySelect = document.getElementById('change_addr_city');

  fetch(`${getApiBaseUrl()}/locations/countries/${countryId}/states/`)
    .then(response => response.json())
    .then(data => {
      stateSelect.innerHTML = '<option value="">Select state/province...</option>';
      citySelect.innerHTML = '<option value="">Select state first...</option>';
      if (data.length > 0) {
        data.forEach(state => {
          const option = document.createElement('option');
          option.value = state.id;
          option.textContent = state.name;
          stateSelect.appendChild(option);
        });
        stateSelect.addEventListener('change', () => loadCitiesForChangeAddress(stateSelect.value));
      } else {
        stateSelect.innerHTML = '<option value="N/A">N/A</option>';
        citySelect.innerHTML = '<option value="">Enter city manually...</option>';
      }
    })
    .catch(error => {
      console.error('Error fetching states:', error);
      stateSelect.innerHTML = '<option value="">Error loading states</option>';
    });
}

function loadCitiesForChangeAddress(stateId) {
  const citySelect = document.getElementById('change_addr_city');

  fetch(`${getApiBaseUrl()}/locations/states/${stateId}/cities/`)
    .then(response => response.json())
    .then(data => {
      citySelect.innerHTML = '<option value="">Select a city...</option>';
      if (data.length > 0) {
        data.forEach(city => {
          const option = document.createElement('option');
          option.value = city.id;
          option.textContent = city.name;
          citySelect.appendChild(option);
        });
      } else {
        citySelect.innerHTML = '<option value="">Enter city manually...</option>';
      }
    })
    .catch(error => {
      console.error('Error fetching cities:', error);
      citySelect.innerHTML = '<option value="">Error loading cities</option>';
    });
}

function saveChangedAddress() {
  // Get form data
  const formData = {
    nickname: document.getElementById('change_addr_nickname').value,
    first_name: document.getElementById('change_addr_first_name').value,
    last_name: document.getElementById('change_addr_last_name').value,
    address1: document.getElementById('change_addr_address1').value,
    address2: document.getElementById('change_addr_address2').value,
    country: document.getElementById('change_addr_country').value,
    province: document.getElementById('change_addr_province').value,
    city: document.getElementById('change_addr_city').value,
    zip: document.getElementById('change_addr_zip').value,
    country_code: document.getElementById('change_addr_country_code').value,
    phone: document.getElementById('change_addr_phone').value,
    instructions: document.getElementById('change_addr_instructions').value,
    set_default: document.getElementById('change_set_default').checked
  };
  
  // Validate required fields
  if (!formData.first_name || !formData.last_name || !formData.address1 || !formData.country || !formData.province || !formData.city || !formData.zip) {
    showNotification('⚠️ Please fill in all required fields', 'warning');
    return;
  }
  
  // Show success message
  showNotification('✅ Address updated successfully for subscription!', 'success');
  closeChangeAddressModal();
  
  // In a real implementation, you would send the data to the backend
  if (window.djangoIntegration) {
    window.djangoIntegration.makeRequest('/customers/subscriptions/change-address/', 'POST', {
      customer_id: customerId,
      subscription_id: currentSubscriptionId,
      address_data: formData
    });
  }
}

// Cutoff Date Management
class CutoffDateManager {
  constructor() {
    this.subscriptionData = new Map();
    this.init();
  }

  init() {
    // Load cutoff dates when page loads
    document.addEventListener('DOMContentLoaded', () => {
      this.loadAllCutoffDates();
    });
  }

  async loadAllCutoffDates() {
    const subscriptionCards = document.querySelectorAll('.subscription-card');
    
    for (const card of subscriptionCards) {
      const subscriptionId = card.dataset.subscriptionId;
      if (subscriptionId) {
        await this.loadCutoffDate(subscriptionId, card);
      }
    }
  }

  async loadCutoffDate(subscriptionId, cardElement) {
    try {
      // Simulate API call - replace with actual API endpoint
      const cutoffData = await this.fetchCutoffDate(subscriptionId);
      this.displayCutoffDate(cardElement, cutoffData);
    } catch (error) {
      console.error('Error loading cutoff date:', error);
      this.displayCutoffDate(cardElement, null);
    }
  }

  async fetchCutoffDate(subscriptionId) {
    // Simulate API response - replace with actual API call
    // In production, this would be: fetch(`/api/subscriptions/${subscriptionId}/cutoff-info/`)
    
    // Mock data for demonstration
    const mockData = {
      '1933365': {
        cutoff_date: '2025-06-27',
        days_until_cutoff: 3,
        urgency: 'urgent',
        message: 'Order cutoff in 3 days'
      },
      '1944521': {
        cutoff_date: '2025-08-08',
        days_until_cutoff: 38,
        urgency: 'normal',
        message: 'Order cutoff in 38 days'
      }
    };

    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 500));
    
    return mockData[subscriptionId] || {
      cutoff_date: null,
      days_until_cutoff: null,
      urgency: 'normal',
      message: 'No cutoff set'
    };
  }

  displayCutoffDate(cardElement, cutoffData) {
    const cutoffDateElement = cardElement.querySelector('.cutoff-date');
    const progressBar = cardElement.querySelector('.cutoff-progress-bar');
    const progressLabel = cardElement.querySelector('.progress-label');
    const progressFill = cardElement.querySelector('.progress-fill');

    if (!cutoffData || !cutoffData.cutoff_date) {
      cutoffDateElement.textContent = 'No cutoff set';
      cutoffDateElement.className = 'cutoff-date normal';
      if (progressBar) progressBar.style.display = 'none';
      return;
    }

    // Format cutoff date
    const cutoffDate = new Date(cutoffData.cutoff_date);
    const formattedDate = cutoffDate.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });

    // Update cutoff date display
    cutoffDateElement.textContent = formattedDate;
    cutoffDateElement.className = `cutoff-date ${cutoffData.urgency}`;

    // Show and update progress bar
    if (progressBar && progressLabel && progressFill) {
      progressBar.style.display = 'block';
      
      if (cutoffData.days_until_cutoff > 0) {
        progressLabel.textContent = `${cutoffData.days_until_cutoff} days left to customize this box`;
        
        // Calculate progress percentage (assuming 14-day window)
        const totalDays = 14;
        const remainingDays = Math.min(cutoffData.days_until_cutoff, totalDays);
        const progressPercentage = (remainingDays / totalDays) * 100;
        
        progressFill.style.width = `${Math.max(5, progressPercentage)}%`;
        
        // Color based on urgency
        if (cutoffData.urgency === 'urgent') {
          progressFill.style.background = 'linear-gradient(90deg, #dc3545, #ff6b6b)';
        } else if (cutoffData.urgency === 'warning') {
          progressFill.style.background = 'linear-gradient(90deg, #ffc107, #ffdb4d)';
        } else {
          progressFill.style.background = 'linear-gradient(90deg, #4CAF50, #66bb6a)';
        }
      } else {
        progressLabel.textContent = 'Cutoff passed';
        progressFill.style.width = '100%';
        progressFill.style.background = 'linear-gradient(90deg, #6c757d, #868e96)';
      }
    }

    // Add tooltip for more information
    this.addTooltip(cutoffDateElement, cutoffData.message);
  }

  addTooltip(element, message) {
    element.title = message;
    element.style.cursor = 'help';
  }

  // Refresh cutoff dates (call this periodically or after user actions)
  async refreshCutoffDates() {
    await this.loadAllCutoffDates();
  }
}

// Renewal Calendar and Timeline Manager
class RenewalCalendarManager {
  constructor() {
    this.currentDate = new Date();
    this.currentMonth = new Date();
    this.timelineView = 'month';
    this.renewalData = new Map();
    this.init();
  }

  init() {
    // Load renewal data for calendar
    this.loadCalendarData();
  }

  async loadCalendarData() {
    try {
      // Get all subscription IDs from the page
      const subscriptionCards = document.querySelectorAll('.subscription-card');
      
      for (const card of subscriptionCards) {
        const subscriptionId = card.dataset.subscriptionId;
        if (subscriptionId && !this.renewalData.has(subscriptionId)) {
          await this.loadSubscriptionRenewalData(subscriptionId);
        }
      }
    } catch (error) {
      console.error('Error loading calendar data:', error);
    }
  }

  async loadSubscriptionRenewalData(subscriptionId) {
    try {
      const response = await fetch(`/api/skips/subscriptions/${subscriptionId}/renewal-info/`);
      const data = await response.json();
      
      if (data.success) {
        this.renewalData.set(subscriptionId, data.renewal_info);
      }
    } catch (error) {
      console.error('Error loading subscription renewal data:', error);
    }
  }

  renderCalendar() {
    const calendarGrid = document.getElementById('renewal-calendar-grid');
    if (!calendarGrid) return;

    const year = this.currentMonth.getFullYear();
    const month = this.currentMonth.getMonth();
    
    // Update month display
    const monthNames = ['January', 'February', 'March', 'April', 'May', 'June',
                       'July', 'August', 'September', 'October', 'November', 'December'];
    document.getElementById('calendar-current-month').textContent = `${monthNames[month]} ${year}`;
    
    // Clear calendar
    calendarGrid.innerHTML = '';
    
    // Add day headers
    const dayHeaders = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    dayHeaders.forEach(day => {
      const header = document.createElement('div');
      header.className = 'calendar-header';
      header.textContent = day;
      calendarGrid.appendChild(header);
    });
    
    // Get first day of month and number of days
    const firstDay = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const daysInPrevMonth = new Date(year, month, 0).getDate();
    
    // Add previous month's trailing days
    for (let i = firstDay - 1; i >= 0; i--) {
      const day = daysInPrevMonth - i;
      const dayElement = this.createCalendarDay(day, true, new Date(year, month - 1, day));
      calendarGrid.appendChild(dayElement);
    }
    
    // Add current month's days
    for (let day = 1; day <= daysInMonth; day++) {
      const currentDate = new Date(year, month, day);
      const dayElement = this.createCalendarDay(day, false, currentDate);
      calendarGrid.appendChild(dayElement);
    }
    
    // Add next month's leading days
    const totalCells = calendarGrid.children.length - 7; // Subtract header row
    const remainingCells = 42 - totalCells; // 6 rows * 7 days - header row
    for (let day = 1; day <= remainingCells; day++) {
      const dayElement = this.createCalendarDay(day, true, new Date(year, month + 1, day));
      calendarGrid.appendChild(dayElement);
    }
  }

  createCalendarDay(day, isOtherMonth, date) {
    const dayElement = document.createElement('div');
    dayElement.className = 'calendar-day';
    if (isOtherMonth) {
      dayElement.classList.add('other-month');
    }
    
    // Check if today
    const today = new Date();
    if (date.toDateString() === today.toDateString()) {
      dayElement.classList.add('today');
    }
    
    // Add day number
    const dayNumber = document.createElement('div');
    dayNumber.className = 'calendar-day-number';
    dayNumber.textContent = day;
    dayElement.appendChild(dayNumber);
    
    // Check for renewal events
    const renewalEvents = this.getRenewalEventsForDate(date);
    if (renewalEvents.length > 0) {
      const hasUrgent = renewalEvents.some(event => event.urgency === 'high');
      const hasRenewal = renewalEvents.some(event => event.type === 'renewal');
      const hasCutoff = renewalEvents.some(event => event.type === 'cutoff');
      
      if (hasUrgent) {
        dayElement.classList.add('urgent');
      } else if (hasRenewal) {
        dayElement.classList.add('renewal-date');
      } else if (hasCutoff) {
        dayElement.classList.add('cutoff-date');
      }
      
      // Add indicator dots
      if (hasRenewal) {
        const indicator = document.createElement('div');
        indicator.className = 'calendar-day-indicator renewal';
        dayElement.appendChild(indicator);
      }
      if (hasCutoff) {
        const indicator = document.createElement('div');
        indicator.className = 'calendar-day-indicator cutoff';
        dayElement.appendChild(indicator);
      }
      
      // Add tooltip
      const tooltip = document.createElement('div');
      tooltip.className = 'calendar-day-tooltip';
      tooltip.innerHTML = renewalEvents.map(event => 
        `<div>${event.subscription}: ${event.description}</div>`
      ).join('');
      dayElement.appendChild(tooltip);
      
      // Add click handler
      dayElement.addEventListener('click', () => {
        this.showDateDetails(date, renewalEvents);
      });
    }
    
    return dayElement;
  }

  getRenewalEventsForDate(date) {
    const events = [];
    
    for (const [subscriptionId, renewalInfo] of this.renewalData) {
      const renewalDate = new Date(renewalInfo.next_billing_date);
      const cutoffDate = new Date(renewalInfo.cutoff_date);
      
      if (date.toDateString() === renewalDate.toDateString()) {
        events.push({
          type: 'renewal',
          subscription: renewalInfo.billing_frequency || 'Subscription',
          description: `Renewal $${renewalInfo.billing_amount}`,
          urgency: renewalInfo.urgency_level,
          subscriptionId: subscriptionId
        });
      }
      
      if (date.toDateString() === cutoffDate.toDateString()) {
        events.push({
          type: 'cutoff',
          subscription: renewalInfo.billing_frequency || 'Subscription',
          description: `Order cutoff`,
          urgency: renewalInfo.urgency_level,
          subscriptionId: subscriptionId
        });
      }
    }
    
    return events;
  }

  showDateDetails(date, events) {
    // Create a simple modal to show date details
    const modal = document.createElement('div');
    modal.style.cssText = `
      position: fixed;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      background: white;
      padding: 1.5rem;
      border-radius: 8px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.2);
      z-index: 2000;
      max-width: 300px;
    `;
    
    modal.innerHTML = `
      <h3 style="margin: 0 0 1rem 0; color: #333;">${date.toLocaleDateString()}</h3>
      ${events.map(event => `
        <div style="margin-bottom: 0.5rem; padding: 0.5rem; background: rgba(0,0,0,0.05); border-radius: 4px;">
          <div style="font-weight: 600; color: #333;">${event.subscription}</div>
          <div style="font-size: 0.9rem; color: #666;">${event.description}</div>
        </div>
      `).join('')}
      <button onclick="this.parentElement.remove()" style="background: #007bff; color: white; border: none; padding: 0.5rem 1rem; border-radius: 4px; cursor: pointer; margin-top: 1rem;">Close</button>
    `;
    
    document.body.appendChild(modal);
    
    // Auto-remove after 10 seconds
    setTimeout(() => {
      if (modal.parentElement) {
        modal.remove();
      }
    }, 10000);
  }

  renderTimeline() {
    const timelineContent = document.getElementById('renewal-timeline-content');
    if (!timelineContent) return;

    // Load predictions
    this.loadRenewalPredictions();
    
    // Update billing summary
    this.updateBillingSummary();
    
    // Get all renewal events sorted by date
    const allEvents = [];
    const today = new Date();
    
    for (const [subscriptionId, renewalInfo] of this.renewalData) {
      const renewalDate = new Date(renewalInfo.next_billing_date);
      const cutoffDate = new Date(renewalInfo.cutoff_date);
      
      allEvents.push({
        date: renewalDate,
        type: 'renewal',
        subscription: renewalInfo.billing_frequency || 'Subscription',
        description: `Renewal $${renewalInfo.billing_amount}`,
        urgency: renewalInfo.urgency_level,
        subscriptionId: subscriptionId,
        daysUntil: Math.ceil((renewalDate - today) / (1000 * 60 * 60 * 24)),
        amount: parseFloat(renewalInfo.billing_amount || '0')
      });
      
      allEvents.push({
        date: cutoffDate,
        type: 'cutoff',
        subscription: renewalInfo.billing_frequency || 'Subscription',
        description: 'Order cutoff - Last day to customize',
        urgency: renewalInfo.urgency_level,
        subscriptionId: subscriptionId,
        daysUntil: Math.ceil((cutoffDate - today) / (1000 * 60 * 60 * 24)),
        amount: 0
      });
    }
    
    // Sort events by date
    allEvents.sort((a, b) => a.date - b.date);
    
    // Filter based on timeline view
    const filteredEvents = this.filterEventsByView(allEvents);
    
    // Render events
    const eventsContainer = document.getElementById('timeline-events-container');
    if (eventsContainer) {
      eventsContainer.innerHTML = '';
      
      filteredEvents.forEach(event => {
        const eventElement = this.createTimelineEvent(event);
        eventsContainer.appendChild(eventElement);
      });
      
      if (filteredEvents.length === 0) {
        eventsContainer.innerHTML = '<div style="text-align: center; padding: 2rem; color: #666;">No events found for the selected period.</div>';
      }
    }
  }

  loadRenewalPredictions() {
    const predictionContent = document.getElementById('prediction-content');
    if (!predictionContent) return;

    // Analyze renewal patterns and make predictions
    const predictions = this.analyzeRenewalPatterns();
    
    predictionContent.innerHTML = `
      <div class="prediction-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1rem;">
        ${predictions.map(prediction => `
          <div class="prediction-card" style="background: rgba(var(--color-background), 0.5); border: 1px solid rgba(var(--color-foreground), 0.1); border-radius: var(--buttons-radius); padding: 1rem;">
            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
              <span style="font-size: 1.5rem;">${prediction.icon}</span>
              <h5 style="margin: 0; color: rgb(var(--color-foreground));">${prediction.title}</h5>
            </div>
            <p style="margin: 0.5rem 0; color: rgba(var(--color-foreground), 0.7); font-size: 0.9rem;">${prediction.description}</p>
            <div style="margin-top: 0.5rem;">
              <span style="font-size: 0.8rem; padding: 0.2rem 0.5rem; background: ${prediction.color}; color: white; border-radius: 12px;">${prediction.confidence}</span>
            </div>
          </div>
        `).join('')}
      </div>
    `;
  }

  analyzeRenewalPatterns() {
    const predictions = [];
    const today = new Date();
    
    // Analyze subscription patterns
    let totalMonthlySpend = 0;
    let highRiskSubscriptions = 0;
    let upcomingRenewals = 0;
    
    for (const [subscriptionId, renewalInfo] of this.renewalData) {
      const amount = parseFloat(renewalInfo.billing_amount || '0');
      const daysUntil = Math.ceil((new Date(renewalInfo.next_billing_date) - today) / (1000 * 60 * 60 * 24));
      
      totalMonthlySpend += amount;
      
      if (renewalInfo.urgency_level === 'high') {
        highRiskSubscriptions++;
      }
      
      if (daysUntil <= 30 && daysUntil > 0) {
        upcomingRenewals++;
      }
    }
    
    // Predict next month spending
    const nextMonthPrediction = totalMonthlySpend * 1.05; // 5% growth estimate
    predictions.push({
      icon: '📈',
      title: 'Next Month Spending',
      description: `Estimated $${nextMonthPrediction.toFixed(2)} based on current subscriptions`,
      confidence: 'High confidence',
      color: '#4CAF50'
    });
    
    // Predict churn risk
    if (highRiskSubscriptions > 0) {
      predictions.push({
        icon: '⚠️',
        title: 'Churn Risk Alert',
        description: `${highRiskSubscriptions} subscription(s) at high risk of cancellation`,
        confidence: 'Medium confidence',
        color: '#ffc107'
      });
    }
    
    // Predict optimal billing timing
    if (upcomingRenewals > 0) {
      predictions.push({
        icon: '🎯',
        title: 'Billing Optimization',
        description: `${upcomingRenewals} renewals in next 30 days - consider consolidating billing dates`,
        confidence: 'High confidence',
        color: '#2196F3'
      });
    }
    
    // Predict annual savings
    const annualSavings = totalMonthlySpend * 12 * 0.1; // 10% potential savings
    predictions.push({
      icon: '💰',
      title: 'Potential Savings',
      description: `Save $${annualSavings.toFixed(2)} annually by optimizing subscription timing`,
      confidence: 'Medium confidence',
      color: '#9C27B0'
    });
    
    return predictions;
  }

  showBillingOptimization() {
    const modal = document.getElementById('billing-optimization-modal');
    if (modal) {
      modal.style.display = 'flex';
      this.loadOptimizationAnalysis();
    }
  }

  loadOptimizationAnalysis() {
    const analysisContainer = document.getElementById('optimization-analysis');
    if (!analysisContainer) return;

    // Calculate optimization opportunities
    const optimization = this.calculateOptimizationOpportunities();
    
    analysisContainer.innerHTML = `
      <div class="optimization-summary" style="background: rgba(var(--color-foreground), 0.05); border-radius: var(--media-radius); padding: 1.5rem; margin-bottom: 2rem;">
        <h4 style="margin: 0 0 1rem 0; color: rgb(var(--color-foreground));">📊 Optimization Summary</h4>
        <div class="summary-stats" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
          <div class="stat-item">
            <div style="font-size: 1.1rem; color: rgba(var(--color-foreground), 0.7);">Current Monthly Spend</div>
            <div style="font-size: 1.4rem; font-weight: 600; color: rgb(var(--color-foreground));">$${optimization.currentSpend.toFixed(2)}</div>
          </div>
          <div class="stat-item">
            <div style="font-size: 1.1rem; color: rgba(var(--color-foreground), 0.7);">Potential Savings</div>
            <div style="font-size: 1.4rem; font-weight: 600; color: #4CAF50;">$${optimization.potentialSavings.toFixed(2)}</div>
          </div>
          <div class="stat-item">
            <div style="font-size: 1.1rem; color: rgba(var(--color-foreground), 0.7);">Optimized Spend</div>
            <div style="font-size: 1.4rem; font-weight: 600; color: rgb(var(--color-foreground));">$${optimization.optimizedSpend.toFixed(2)}</div>
          </div>
        </div>
      </div>
      
      <div class="optimization-recommendations" style="background: rgba(var(--color-button), 0.05); border-radius: var(--media-radius); padding: 1.5rem;">
        <h4 style="margin: 0 0 1rem 0; color: rgb(var(--color-foreground));">💡 Recommendations</h4>
        <div class="recommendations-list">
          ${optimization.recommendations.map(rec => `
            <div class="recommendation-item" style="display: flex; align-items: flex-start; gap: 1rem; padding: 1rem; background: rgba(var(--color-background), 0.5); border-radius: var(--buttons-radius); margin-bottom: 1rem;">
              <span style="font-size: 1.5rem;">${rec.icon}</span>
              <div style="flex: 1;">
                <h5 style="margin: 0 0 0.5rem 0; color: rgb(var(--color-foreground));">${rec.title}</h5>
                <p style="margin: 0; color: rgba(var(--color-foreground), 0.7); font-size: 0.9rem;">${rec.description}</p>
                <div style="margin-top: 0.5rem;">
                  <span style="font-size: 0.8rem; padding: 0.2rem 0.5rem; background: ${rec.impact === 'High' ? '#4CAF50' : rec.impact === 'Medium' ? '#ffc107' : '#2196F3'}; color: white; border-radius: 12px;">${rec.impact} impact</span>
                </div>
              </div>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  }

  calculateOptimizationOpportunities() {
    let currentSpend = 0;
    const recommendations = [];
    
    for (const [subscriptionId, renewalInfo] of this.renewalData) {
      const amount = parseFloat(renewalInfo.billing_amount || '0');
      currentSpend += amount;
      
      // Analyze each subscription for optimization opportunities
      const frequency = renewalInfo.billing_frequency || 'monthly';
      
      if (frequency.includes('monthly') && amount > 50) {
        recommendations.push({
          icon: '📅',
          title: 'Switch to Annual Billing',
          description: `Save 10% by switching this subscription to annual billing ($${(amount * 0.1).toFixed(2)} savings)`,
          impact: 'High',
          subscriptionId: subscriptionId
        });
      }
      
      if (renewalInfo.urgency_level === 'high') {
        recommendations.push({
          icon: '⏰',
          title: 'Align Billing Dates',
          description: 'Move this subscription to align with other billing dates for better cash flow management',
          impact: 'Medium',
          subscriptionId: subscriptionId
        });
      }
    }
    
    // Calculate potential savings
    const potentialSavings = recommendations.reduce((total, rec) => {
      if (rec.title.includes('Annual')) {
        const savingsMatch = rec.description.match(/\$\d+\.\d+/);
        if (savingsMatch) {
          return total + parseFloat(savingsMatch[0].replace('$', ''));
        }
      }
      return total;
    }, 0);
    
    return {
      currentSpend,
      potentialSavings,
      optimizedSpend: currentSpend - potentialSavings,
      recommendations
    };
  }

  updateBillingSummary() {
    const today = new Date();
    let monthTotal = 0;
    let quarterTotal = 0;
    let yearTotal = 0;
    let activeCount = 0;
    
    for (const [subscriptionId, renewalInfo] of this.renewalData) {
      const renewalDate = new Date(renewalInfo.next_billing_date);
      const amount = parseFloat(renewalInfo.billing_amount || '0');
      
      // Count active subscriptions
      if (renewalInfo.urgency_level !== 'cancelled') {
        activeCount++;
      }
      
      // Calculate totals based on billing frequency
      const frequency = renewalInfo.billing_frequency || 'monthly';
      const intervalCount = parseInt(renewalInfo.billing_frequency?.split(' ')[0] || '1');
      
      // Monthly total
      if (renewalDate.getMonth() === today.getMonth() && renewalDate.getFullYear() === today.getFullYear()) {
        monthTotal += amount;
      }
      
      // Quarterly total
      const currentQuarter = Math.floor(today.getMonth() / 3);
      const eventQuarter = Math.floor(renewalDate.getMonth() / 3);
      if (eventQuarter === currentQuarter && renewalDate.getFullYear() === today.getFullYear()) {
        quarterTotal += amount;
      }
      
      // Yearly total
      if (renewalDate.getFullYear() === today.getFullYear()) {
        yearTotal += amount;
      }
    }
    
    // Update summary display
    this.updateSummaryDisplay('summary-month', monthTotal);
    this.updateSummaryDisplay('summary-quarter', quarterTotal);
    this.updateSummaryDisplay('summary-year', yearTotal);
    this.updateSummaryDisplay('summary-count', activeCount, false);
  }

  updateSummaryDisplay(elementId, value, isCurrency = true) {
    const element = document.getElementById(elementId);
    if (element) {
      element.textContent = isCurrency ? `$${value.toFixed(2)}` : value.toString();
    }
  }

  filterEventsByView(events) {
    const today = new Date();
    let startDate, endDate;
    
    switch (this.timelineView) {
      case 'month':
        startDate = new Date(today.getFullYear(), today.getMonth(), 1);
        endDate = new Date(today.getFullYear(), today.getMonth() + 1, 0);
        break;
      case 'quarter':
        const currentQuarter = Math.floor(today.getMonth() / 3);
        startDate = new Date(today.getFullYear(), currentQuarter * 3, 1);
        endDate = new Date(today.getFullYear(), currentQuarter * 3 + 3, 0);
        break;
      case 'year':
        startDate = new Date(today.getFullYear(), 0, 1);
        endDate = new Date(today.getFullYear(), 11, 31);
        break;
    }
    
    return events.filter(event => event.date >= startDate && event.date <= endDate);
  }

  createTimelineEvent(event) {
    const eventElement = document.createElement('div');
    eventElement.className = 'timeline-item';
    
    if (event.urgency === 'high') {
      eventElement.classList.add('urgent');
    } else if (event.daysUntil <= 14) {
      eventElement.classList.add('upcoming');
    }
    
    eventElement.innerHTML = `
      <div class="timeline-date">
        <div>${event.date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</div>
        <div style="font-size: 0.8rem; opacity: 0.7;">${event.date.toLocaleDateString('en-US', { weekday: 'short' })}</div>
      </div>
      <div class="timeline-content-item">
        <div class="timeline-title">${event.subscription}</div>
        <div class="timeline-details">
          <span>${event.description}</span>
          <span>${event.daysUntil > 0 ? `in ${event.daysUntil} days` : event.daysUntil === 0 ? 'today' : `${Math.abs(event.daysUntil)} days ago`}</span>
        </div>
        <div class="timeline-actions">
          <button class="timeline-action-btn" onclick="window.renewalDisplayManager.refreshSubscription('${event.subscriptionId}')">Refresh</button>
          <button class="timeline-action-btn" onclick="window.showTab('subscriptions')">Manage</button>
        </div>
      </div>
    `;
    
    return eventElement;
  }

  changeMonth(direction) {
    this.currentMonth.setMonth(this.currentMonth.getMonth() + direction);
    this.renderCalendar();
  }

  resetToToday() {
    this.currentMonth = new Date();
    this.renderCalendar();
  }

  setTimelineView(view) {
    this.timelineView = view;
    
    // Update button states
    document.querySelectorAll('.timeline-view-btn').forEach(btn => {
      btn.classList.remove('active');
      if (btn.dataset.view === view) {
        btn.classList.add('active');
      }
    });
    
    this.renderTimeline();
  }

  exportCalendar() {
    // Simple export functionality
    const events = [];
    const today = new Date();
    
    for (const [subscriptionId, renewalInfo] of this.renewalData) {
      const renewalDate = new Date(renewalInfo.next_billing_date);
      const cutoffDate = new Date(renewalInfo.cutoff_date);
      
      events.push({
        date: renewalDate.toISOString().split('T')[0],
        type: 'renewal',
        subscription: renewalInfo.billing_frequency || 'Subscription',
        amount: renewalInfo.billing_amount
      });
      
      events.push({
        date: cutoffDate.toISOString().split('T')[0],
        type: 'cutoff',
        subscription: renewalInfo.billing_frequency || 'Subscription'
      });
    }
    
    const csv = 'Date,Type,Subscription,Amount\n' + 
      events.map(event => `${event.date},${event.type},${event.subscription},${event.amount || ''}`).join('\n');
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'renewal-calendar.csv';
    a.click();
    window.URL.revokeObjectURL(url);
  }

  exportTimeline() {
    // Similar to exportCalendar but for timeline view
    this.exportCalendar();
  }

  // Reminder functionality
  saveReminderSettings() {
    const emailEnabled = document.getElementById('reminder-email')?.checked || false;
    const smsEnabled = document.getElementById('reminder-sms')?.checked || false;
    const reminderDays = document.getElementById('reminder-days')?.value || '3';
    
    const settings = {
      email: emailEnabled,
      sms: smsEnabled,
      days_before: parseInt(reminderDays)
    };
    
    // Save to localStorage (in production, this would be saved to backend)
    localStorage.setItem('renewal_reminder_settings', JSON.stringify(settings));
    
    // Show confirmation
    this.showNotification('Reminder settings saved successfully!', 'success');
    
    // Schedule reminders for upcoming renewals
    this.scheduleReminders();
  }

  loadReminderSettings() {
    const saved = localStorage.getItem('renewal_reminder_settings');
    if (saved) {
      const settings = JSON.parse(saved);
      
      const emailCheckbox = document.getElementById('reminder-email');
      const smsCheckbox = document.getElementById('reminder-sms');
      const daysSelect = document.getElementById('reminder-days');
      
      if (emailCheckbox) emailCheckbox.checked = settings.email || false;
      if (smsCheckbox) smsCheckbox.checked = settings.sms || false;
      if (daysSelect) daysSelect.value = settings.days_before || '3';
    }
  }

  scheduleReminders() {
    const settings = JSON.parse(localStorage.getItem('renewal_reminder_settings') || '{}');
    
    if (!settings.email && !settings.sms) return;
    
    const today = new Date();
    const reminderDate = new Date(today);
    reminderDate.setDate(today.getDate() + parseInt(settings.days_before || 3));
    
    // Check for renewals within the reminder period
    for (const [subscriptionId, renewalInfo] of this.renewalData) {
      const renewalDate = new Date(renewalInfo.next_billing_date);
      const daysUntil = Math.ceil((renewalDate - today) / (1000 * 60 * 60 * 24));
      
      if (daysUntil <= parseInt(settings.days_before || 3) && daysUntil > 0) {
        this.scheduleReminder(subscriptionId, renewalInfo, daysUntil);
      }
    }
  }

  scheduleReminder(subscriptionId, renewalInfo, daysUntil) {
    const settings = JSON.parse(localStorage.getItem('renewal_reminder_settings') || '{}');
    
    // In production, this would make API calls to schedule actual reminders
    console.log(`Scheduling reminder for ${renewalInfo.billing_frequency} in ${daysUntil} days`);
    
    // Show notification for demo purposes
    this.showNotification(`Reminder scheduled: ${renewalInfo.billing_frequency} renewal in ${daysUntil} days`, 'info');
  }

  showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    // Style the notification
    notification.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      padding: 15px 20px;
      border-radius: 8px;
      color: white;
      font-weight: 500;
      z-index: 10000;
      max-width: 300px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
      transform: translateX(100%);
      transition: transform 0.3s ease;
    `;
    
    // Set background color based on type
    switch (type) {
      case 'success':
        notification.style.backgroundColor = '#4CAF50';
        break;
      case 'error':
        notification.style.backgroundColor = '#f44336';
        break;
      case 'warning':
        notification.style.backgroundColor = '#ff9800';
        break;
      default:
        notification.style.backgroundColor = '#2196F3';
    }
    
    // Add to page
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
      notification.style.transform = 'translateX(0)';
    }, 100);
    
    // Remove after 5 seconds
    setTimeout(() => {
      notification.style.transform = 'translateX(100%)';
      setTimeout(() => {
        if (notification.parentNode) {
          notification.parentNode.removeChild(notification);
        }
      }, 300);
    }, 5000);
  }
}

// Global functions for calendar and timeline
window.showRenewalCalendar = function() {
  const modal = document.getElementById('renewal-calendar-modal');
  if (modal) {
    modal.style.display = 'flex';
    window.renewalCalendarManager.renderCalendar();
  }
};

window.closeRenewalCalendar = function() {
  const modal = document.getElementById('renewal-calendar-modal');
  if (modal) {
    modal.style.display = 'none';
  }
};

window.showRenewalTimeline = function() {
  const modal = document.getElementById('renewal-timeline-modal');
  if (modal) {
    modal.style.display = 'flex';
    window.renewalCalendarManager.renderTimeline();
  }
};

window.closeRenewalTimeline = function() {
  const modal = document.getElementById('renewal-timeline-modal');
  if (modal) {
    modal.style.display = 'none';
  }
};

window.changeCalendarMonth = function(direction) {
  window.renewalCalendarManager.changeMonth(direction);
};

window.resetCalendarToToday = function() {
  window.renewalCalendarManager.resetToToday();
};

window.setTimelineView = function(view) {
  window.renewalCalendarManager.setTimelineView(view);
};

window.exportRenewalCalendar = function() {
  window.renewalCalendarManager.exportCalendar();
};

window.exportTimeline = function() {
  window.renewalCalendarManager.exportTimeline();
};

window.refreshTimeline = function() {
  window.renewalCalendarManager.loadCalendarData().then(() => {
    window.renewalCalendarManager.renderTimeline();
  });
};

window.saveReminderSettings = function() {
  window.renewalCalendarManager.saveReminderSettings();
};

window.showBillingOptimization = function() {
  window.renewalCalendarManager.showBillingOptimization();
};

window.closeBillingOptimization = function() {
  const modal = document.getElementById('billing-optimization-modal');
  if (modal) {
    modal.style.display = 'none';
  }
};

// Initialize renewal calendar manager
const renewalCalendarManager = new RenewalCalendarManager();

// Make it globally available
window.renewalCalendarManager = renewalCalendarManager;

// Renewal Display Manager
class RenewalDisplayManager {
  constructor() {
    this.baseApiUrl = '/api/skips/subscriptions';
    this.renewalData = new Map();
    this.init();
  }

  init() {
    // Load renewal data for all subscriptions
    this.loadAllRenewalData();
    
    // Set up periodic refresh
    setInterval(() => {
      this.refreshAllRenewalData();
    }, 60000); // Refresh every minute
  }

  async loadAllRenewalData() {
    // Get all subscription cards
    const subscriptionCards = document.querySelectorAll('.subscription-card');
    
    for (const card of subscriptionCards) {
      const subscriptionId = card.dataset.subscriptionId;
      if (subscriptionId) {
        await this.loadRenewalData(subscriptionId);
      }
    }
  }

  async loadRenewalData(subscriptionId) {
    try {
      // Get renewal info
      const response = await fetch(`${this.baseApiUrl}/${subscriptionId}/renewal-info/`);
      const data = await response.json();
      
      if (data.success) {
        this.renewalData.set(subscriptionId, data.renewal_info);
        this.updateRenewalDisplay(subscriptionId, data.renewal_info);
      }
    } catch (error) {
      console.error('Error loading renewal data:', error);
      this.displayRenewalError(subscriptionId);
    }
  }

  updateRenewalDisplay(subscriptionId, renewalInfo) {
    // Update urgency badge
    const urgencyElement = document.getElementById(`renewal-urgency-${subscriptionId}`);
    if (urgencyElement) {
      urgencyElement.textContent = renewalInfo.urgency_text;
      urgencyElement.className = `renewal-urgency ${renewalInfo.urgency_level}`;
    }

    // Update progress bar
    this.updateProgressBar(subscriptionId, renewalInfo.cycle_progress);
  }

  calculateRenewalUrgency(nextBillingDate) {
    const now = new Date();
    const renewalDate = new Date(nextBillingDate);
    const daysUntil = Math.ceil((renewalDate - now) / (1000 * 60 * 60 * 24));
    
    if (daysUntil <= 3) {
      return {
        level: 'high',
        text: `${daysUntil} days`,
        message: 'Renewal imminent - Action required'
      };
    } else if (daysUntil <= 7) {
      return {
        level: 'medium',
        text: `${daysUntil} days`,
        message: 'Renewal approaching - Be prepared'
      };
    } else {
      return {
        level: 'low',
        text: `${daysUntil} days`,
        message: 'Renewal scheduled - No action needed'
      };
    }
  }

  updateProgressBar(subscriptionId, progressData) {
    const progressFill = document.getElementById(`renewal-progress-fill-${subscriptionId}`);
    const progressLabel = document.getElementById(`renewal-progress-label-${subscriptionId}`);
    
    if (progressFill && progressLabel) {
      // Update progress bar
      progressFill.style.width = `${progressData.percentage}%`;
      
      // Update color based on progress
      progressFill.className = 'progress-fill';
      if (progressData.percentage >= 85) {
        progressFill.classList.add('urgent');
      } else if (progressData.percentage >= 70) {
        progressFill.classList.add('warning');
      } else {
        progressFill.classList.add('good');
      }
      
      // Update label
      progressLabel.textContent = `${progressData.days_remaining} days left in cycle (${Math.round(progressData.percentage)}% complete)`;
    }
  }

  displayRenewalError(subscriptionId) {
    const urgencyElement = document.getElementById(`renewal-urgency-${subscriptionId}`);
    const progressLabel = document.getElementById(`renewal-progress-label-${subscriptionId}`);
    
    if (urgencyElement) {
      urgencyElement.textContent = 'Error';
      urgencyElement.className = 'renewal-urgency calculating';
    }
    
    if (progressLabel) {
      progressLabel.textContent = 'Unable to load renewal data';
    }
  }

  async refreshAllRenewalData() {
    for (const subscriptionId of this.renewalData.keys()) {
      await this.loadRenewalData(subscriptionId);
    }
  }

  // Public method to manually refresh a specific subscription
  async refreshSubscription(subscriptionId) {
    await this.loadRenewalData(subscriptionId);
  }

  // Get renewal data for other components
  getRenewalData(subscriptionId) {
    return this.renewalData.get(subscriptionId);
  }

  // Calculate next renewal date with cutoff consideration
  getNextRenewalWithCutoff(subscriptionId) {
    const subscription = this.renewalData.get(subscriptionId);
    if (!subscription) return null;
    
    const renewalDate = new Date(subscription.next_billing_date);
    const cutoffDate = new Date(renewalDate);
    cutoffDate.setDate(cutoffDate.getDate() - 14); // 14 days before renewal
    
    return {
      renewalDate: renewalDate,
      cutoffDate: cutoffDate,
      daysUntilRenewal: Math.ceil((renewalDate - new Date()) / (1000 * 60 * 60 * 24)),
      daysUntilCutoff: Math.ceil((cutoffDate - new Date()) / (1000 * 60 * 60 * 24))
    };
  }
}

// Initialize renewal display manager
const renewalDisplayManager = new RenewalDisplayManager();

// Make it globally available for other scripts
window.renewalDisplayManager = renewalDisplayManager;

// Initialize cutoff date manager
const cutoffDateManager = new CutoffDateManager();

// Make it globally available for other scripts
window.cutoffDateManager = cutoffDateManager;

// Subscription Management Functions
class SubscriptionManager {
  constructor() {
    this.baseApiUrl = '/api/skips/subscriptions';
  }

  async cancelSubscription(subscriptionId, reason, feedback) {
    try {
      // First check if cancellation is allowed
      const optionsData = await this.getSubscriptionOptions(subscriptionId);
      
      if (optionsData && optionsData.success) {
        const options = optionsData.options;
        
        if (options.cancellation_blocked) {
          this.showNotification(options.cancellation_block_reason, 'error');
          return;
        }
      }
      
      const response = await fetch(`${this.baseApiUrl}/cancel/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': this.getCsrfToken()
        },
        body: JSON.stringify({
          subscription_id: subscriptionId,
          reason: reason,
          feedback: feedback,
          confirm: true
        })
      });

      const data = await response.json();
      
      if (data.success) {
        this.showNotification('Subscription cancelled successfully', 'success');
        // Refresh subscription data
        setTimeout(() => {
          window.location.reload();
        }, 2000);
      } else {
        this.showNotification(data.error || 'Failed to cancel subscription', 'error');
        
        // If the error is about pending skips, update the button state
        if (data.error && data.error.includes('pending skip')) {
          this.updateCancellationButton(subscriptionId);
        }
      }
    } catch (error) {
      console.error('Error cancelling subscription:', error);
      this.showNotification('An error occurred while cancelling subscription', 'error');
    }
  }

  async pauseSubscription(subscriptionId, durationMonths, reason) {
    try {
      const response = await fetch(`${this.baseApiUrl}/pause/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': this.getCsrfToken()
        },
        body: JSON.stringify({
          subscription_id: subscriptionId,
          duration_months: durationMonths,
          reason: reason
        })
      });

      const data = await response.json();
      
      if (data.success) {
        this.showNotification(`Subscription paused for ${durationMonths} month(s)`, 'success');
        // Refresh subscription data
        setTimeout(() => {
          window.location.reload();
        }, 2000);
      } else {
        this.showNotification(data.error || 'Failed to pause subscription', 'error');
      }
    } catch (error) {
      console.error('Error pausing subscription:', error);
      this.showNotification('An error occurred while pausing subscription', 'error');
    }
  }

  async resumeSubscription(subscriptionId) {
    try {
      const response = await fetch(`${this.baseApiUrl}/resume/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': this.getCsrfToken()
        },
        body: JSON.stringify({
          subscription_id: subscriptionId
        })
      });

      const data = await response.json();
      
      if (data.success) {
        this.showNotification('Subscription resumed successfully', 'success');
        // Refresh subscription data
        setTimeout(() => {
          window.location.reload();
        }, 2000);
      } else {
        this.showNotification(data.error || 'Failed to resume subscription', 'error');
      }
    } catch (error) {
      console.error('Error resuming subscription:', error);
      this.showNotification('An error occurred while resuming subscription', 'error');
    }
  }

  async changeFrequency(subscriptionId, newInterval, newIntervalCount) {
    try {
      const response = await fetch(`${this.baseApiUrl}/change-frequency/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': this.getCsrfToken()
        },
        body: JSON.stringify({
          subscription_id: subscriptionId,
          new_interval: newInterval,
          new_interval_count: newIntervalCount
        })
      });

      const data = await response.json();
      
      if (data.success) {
        this.showNotification('Billing frequency changed successfully', 'success');
        // Refresh subscription data
        setTimeout(() => {
          window.location.reload();
        }, 2000);
      } else {
        this.showNotification(data.error || 'Failed to change billing frequency', 'error');
      }
    } catch (error) {
      console.error('Error changing frequency:', error);
      this.showNotification('An error occurred while changing frequency', 'error');
    }
  }

  async getSubscriptionOptions(subscriptionId) {
    try {
      const response = await fetch(`${this.baseApiUrl}/${subscriptionId}/options/`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error getting subscription options:', error);
      return null;
    }
  }

  async updateCancellationButton(subscriptionId) {
    try {
      const optionsData = await this.getSubscriptionOptions(subscriptionId);
      
      if (optionsData && optionsData.success) {
        const options = optionsData.options;
        const cancelBtn = document.querySelector(`[onclick*="cancelSubscription('${subscriptionId}')"]`);
        
        if (cancelBtn) {
          if (options.cancellation_blocked) {
            // Disable the cancellation button
            cancelBtn.disabled = true;
            cancelBtn.style.opacity = '0.5';
            cancelBtn.style.cursor = 'not-allowed';
            cancelBtn.title = options.cancellation_block_reason;
            
            // Add visual indicator
            const warningIcon = document.createElement('span');
            warningIcon.innerHTML = ' ⚠️';
            warningIcon.style.color = '#ffc107';
            cancelBtn.parentNode.insertBefore(warningIcon, cancelBtn);
            
            // Show notification
            this.showNotification(options.cancellation_block_reason, 'warning');
          } else {
            // Enable the cancellation button
            cancelBtn.disabled = false;
            cancelBtn.style.opacity = '1';
            cancelBtn.style.cursor = 'pointer';
            cancelBtn.title = '';
            
            // Remove warning icon if exists
            const warningIcon = cancelBtn.parentNode.querySelector('span[style*="color: #ffc107"]');
            if (warningIcon) {
              warningIcon.remove();
            }
          }
        }
      }
    } catch (error) {
      console.error('Error updating cancellation button:', error);
    }
  }

  getCsrfToken() {
    // Try to get CSRF token from cookie
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
      const [name, value] = cookie.trim().split('=');
      if (name === 'csrftoken') {
        return decodeURIComponent(value);
      }
    }
    // Fallback to meta tag
    const metaTag = document.querySelector('meta[name="csrf-token"]');
    return metaTag ? metaTag.getAttribute('content') : '';
  }

  showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    // Style the notification
    notification.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      padding: 15px 20px;
      border-radius: 8px;
      color: white;
      font-weight: 500;
      z-index: 10000;
      max-width: 300px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
      transform: translateX(100%);
      transition: transform 0.3s ease;
    `;
    
    // Set background color based on type
    switch (type) {
      case 'success':
        notification.style.backgroundColor = '#4CAF50';
        break;
      case 'error':
        notification.style.backgroundColor = '#f44336';
        break;
      case 'warning':
        notification.style.backgroundColor = '#ff9800';
        break;
      default:
        notification.style.backgroundColor = '#2196F3';
    }
    
    // Add to page
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
      notification.style.transform = 'translateX(0)';
    }, 100);
    
    // Remove after 5 seconds
    setTimeout(() => {
      notification.style.transform = 'translateX(100%)';
      setTimeout(() => {
        if (notification.parentNode) {
          notification.parentNode.removeChild(notification);
        }
      }, 300);
    }, 5000);
  }
}

// Initialize subscription manager
const subscriptionManager = new SubscriptionManager();

// Make it globally available for other scripts
window.subscriptionManager = subscriptionManager;

// Initialize cancellation button states when page loads
document.addEventListener('DOMContentLoaded', function() {
  // Find all subscription cards and update their cancellation buttons
  const subscriptionCards = document.querySelectorAll('.subscription-card');
  
  subscriptionCards.forEach(card => {
    const subscriptionId = card.dataset.subscriptionId;
    if (subscriptionId) {
      subscriptionManager.updateCancellationButton(subscriptionId);
    }
  });
});

// Global functions for onclick handlers
window.confirmCancellation = function() {
  const subscriptionId = document.querySelector('#cancel-subscription-modal input[name="subscription_id"]')?.value;
  const reason = document.querySelector('#cancel-subscription-modal select[name="reason"]')?.value;
  const feedback = document.querySelector('#cancel-subscription-modal textarea[name="feedback"]')?.value;
  
  if (!subscriptionId) {
    subscriptionManager.showNotification('Subscription ID not found', 'error');
    return;
  }
  
  if (!reason) {
    subscriptionManager.showNotification('Please select a reason for cancellation', 'error');
    return;
  }
  
  subscriptionManager.cancelSubscription(subscriptionId, reason, feedback);
};

window.cancelSubscription = function(subscriptionId) {
  // Set the subscription ID in the modal
  const subscriptionIdInput = document.querySelector('#cancel-subscription-modal input[name="subscription_id"]');
  if (subscriptionIdInput) {
    subscriptionIdInput.value = subscriptionId;
  }
  
  // Update the subscription name in the modal
  const subscriptionNameElement = document.querySelector('#cancel-subscription-name');
  if (subscriptionNameElement) {
    const subscriptionCard = document.querySelector(`[data-subscription-id="${subscriptionId}"]`);
    if (subscriptionCard) {
      const subscriptionName = subscriptionCard.querySelector('h3')?.textContent || 'Subscription';
      subscriptionNameElement.textContent = subscriptionName;
    }
  }
  
  // Show the modal
  const modal = document.getElementById('cancel-subscription-modal');
  if (modal) {
    modal.style.display = 'flex';
  }
};

window.closeCancelSubscriptionModal = function() {
  const modal = document.getElementById('cancel-subscription-modal');
  if (modal) {
    modal.style.display = 'none';
  }
};

window.pauseInstead = function() {
  const subscriptionId = document.querySelector('#cancellation-modal input[name="subscription_id"]')?.value;
  const duration = 2; // Default 2 months
  const reason = 'Customer requested pause instead of cancellation';
  
  if (!subscriptionId) {
    subscriptionManager.showNotification('Subscription ID not found', 'error');
    return;
  }
  
  subscriptionManager.pauseSubscription(subscriptionId, duration, reason);
  
  // Close cancellation modal
  const modal = document.getElementById('cancellation-modal');
  if (modal) {
    modal.style.display = 'none';
  }
};

window.changeFrequency = function() {
  const subscriptionId = document.querySelector('#cancellation-modal input[name="subscription_id"]')?.value;
  
  if (!subscriptionId) {
    subscriptionManager.showNotification('Subscription ID not found', 'error');
    return;
  }
  
  // Get subscription options to show available frequencies
  subscriptionManager.getSubscriptionOptions(subscriptionId).then(data => {
    if (data && data.success && data.options) {
      // Show frequency change modal with available options
      showFrequencyChangeModal(subscriptionId, data.options.available_frequencies);
    } else {
      subscriptionManager.showNotification('Failed to load frequency options', 'error');
    }
  });
  
  // Close cancellation modal
  const modal = document.getElementById('cancellation-modal');
  if (modal) {
    modal.style.display = 'none';
  }
};

function showFrequencyChangeModal(subscriptionId, frequencies) {
  // Create modal if it doesn't exist
  let modal = document.getElementById('frequency-change-modal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'frequency-change-modal';
    modal.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(0,0,0,0.5);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 1000;
    `;
    
    modal.innerHTML = `
      <div style="background: white; padding: 30px; border-radius: 12px; max-width: 500px; width: 90%;">
        <h2 style="margin-bottom: 20px;">Change Billing Frequency</h2>
        <p style="margin-bottom: 20px; color: #666;">Select how often you'd like to receive your subscription:</p>
        <div id="frequency-options" style="margin-bottom: 20px;"></div>
        <div style="display: flex; gap: 10px; justify-content: flex-end;">
          <button onclick="closeFrequencyChangeModal()" style="background: #f5f5f5; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer;">Cancel</button>
        </div>
      </div>
    `;
    
    document.body.appendChild(modal);
  }
  
  // Populate frequency options
  const optionsContainer = modal.querySelector('#frequency-options');
  optionsContainer.innerHTML = '';
  
  frequencies.forEach(freq => {
    const option = document.createElement('div');
    option.style.cssText = `
      padding: 15px;
      border: 1px solid #ddd;
      border-radius: 8px;
      margin-bottom: 10px;
      cursor: pointer;
      transition: all 0.2s;
    `;
    
    option.innerHTML = `
      <div style="font-weight: 600; margin-bottom: 5px;">${freq.label}</div>
      <div style="font-size: 14px; color: #666;">Billed every ${freq.count} ${freq.interval.toLowerCase()}(s)</div>
    `;
    
    option.addEventListener('click', () => {
      subscriptionManager.changeFrequency(subscriptionId, freq.interval, freq.count);
      closeFrequencyChangeModal();
    });
    
    option.addEventListener('mouseenter', () => {
      option.style.backgroundColor = '#f8f9fa';
      option.style.borderColor = '#007bff';
    });
    
    option.addEventListener('mouseleave', () => {
      option.style.backgroundColor = 'white';
      option.style.borderColor = '#ddd';
    });
    
    optionsContainer.appendChild(option);
  });
  
  modal.style.display = 'flex';
}

window.closeFrequencyChangeModal = function() {
  const modal = document.getElementById('frequency-change-modal');
  if (modal) {
    modal.style.display = 'none';
  }
};
