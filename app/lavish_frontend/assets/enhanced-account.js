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
