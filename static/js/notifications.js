// Notification Management System
// Handles Web Push Notifications

console.log('Notifications.js loaded');

document.addEventListener('DOMContentLoaded', function () {
    const enableBtn = document.getElementById('enable-notifications');
    const disableBtn = document.getElementById('disable-notifications');
    const batchSelect = document.getElementById('notification-batch');
    const statusText = document.querySelector('.notification-status');

    let swRegistration = null;

    // Check if browser supports notifications
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
        console.warn('Push notifications not supported');
        if (enableBtn) {
            enableBtn.disabled = true;
            enableBtn.textContent = 'Not Supported';
            if (statusText) {
                statusText.textContent = 'Your browser doesn\'t support notifications';
            }
        }
        return;
    }

    // Register Service Worker
    navigator.serviceWorker.register('/static/js/sw.js')
        .then(function (registration) {
            console.log('Service Worker registered:', registration);
            swRegistration = registration;
            checkSubscription();
        })
        .catch(function (error) {
            console.error('Service Worker registration failed:', error);
            if (statusText) {
                statusText.textContent = 'Failed to enable notifications';
            }
        });

    // Check existing subscription
    function checkSubscription() {
        if (!swRegistration) return;

        swRegistration.pushManager.getSubscription()
            .then(function (subscription) {
                if (subscription) {
                    const savedBatch = localStorage.getItem('notification-batch');
                    if (savedBatch && batchSelect && enableBtn && disableBtn && statusText) {
                        batchSelect.value = savedBatch;
                        enableBtn.style.display = 'none';
                        disableBtn.style.display = 'block';
                        statusText.textContent = `✓ Alerts enabled for ${savedBatch} batch`;
                    }
                }
            })
            .catch(function (error) {
                console.error('Error checking subscription:', error);
            });
    }

    // Enable Notifications
    if (enableBtn) {
        enableBtn.addEventListener('click', async function () {
            const selectedBatch = batchSelect ? batchSelect.value.trim() : '';

            if (!selectedBatch) {
                alert('Please select your batch first!');
                return;
            }

            try {
                // Show loading state
                enableBtn.disabled = true;
                enableBtn.innerHTML = '<i class="bi bi-hourglass-split me-1"></i> Enabling...';

                // Request notification permission
                const permission = await Notification.requestPermission();

                if (permission !== 'granted') {
                    alert('Please enable notifications in your browser settings to receive job alerts.');
                    enableBtn.disabled = false;
                    enableBtn.innerHTML = '<i class="bi bi-bell me-1"></i> Enable Alerts';
                    return;
                }

                // Get VAPID public key from server
                const keyResponse = await fetch('/api/vapid-public-key');
                if (!keyResponse.ok) {
                    throw new Error('Failed to get VAPID key');
                }
                const keyData = await keyResponse.json();

                // Subscribe to push notifications
                const subscription = await swRegistration.pushManager.subscribe({
                    userVisibleOnly: true,
                    applicationServerKey: urlBase64ToUint8Array(keyData.publicKey)
                });

                console.log('Push subscription:', subscription);

                // Validate subscription and send to the server
                const subscriptionData = {
                    subscription: subscription.toJSON(),
                    batch: selectedBatch
                };
                console.log('Data being sent to server:', JSON.stringify(subscriptionData));

                const subscribeResponse = await fetch('/api/subscribe', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(subscriptionData)
                });

                if (!subscribeResponse.ok) {
                    throw new Error('Failed to save subscription on server');
                }

                const result = await subscribeResponse.json();
                console.log('Subscription saved:', result);

                // Save batch preference
                localStorage.setItem('notification-batch', selectedBatch);
                localStorage.setItem('notification-endpoint', subscription.endpoint);

                // Update UI
                enableBtn.style.display = 'none';
                disableBtn.style.display = 'block';
                if (statusText) {
                    statusText.textContent = `✓ Alerts enabled for ${selectedBatch} batch`;
                }

                // Show success notification
                showLocalNotification(
                    '🎉 Job Alerts Enabled!',
                    `You'll receive notifications for ${selectedBatch} batch opportunities`
                );

            } catch (error) {
                console.error('Error enabling notifications:', error);
                alert('Failed to enable notifications. Please try again or check your browser settings.');

                // Reset button state
                enableBtn.disabled = false;
                enableBtn.innerHTML = '<i class="bi bi-bell me-1"></i> Enable Alerts';
            }
        });
    }

    // Disable Notifications
    if (disableBtn) {
        disableBtn.addEventListener('click', async function () {
            try {
                disableBtn.disabled = true;
                disableBtn.innerHTML = '<i class="bi bi-hourglass-split me-1"></i> Disabling...';

                const subscription = await swRegistration.pushManager.getSubscription();

                if (subscription) {
                    // Notify server first
                    await fetch('/api/unsubscribe', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            endpoint: subscription.endpoint
                        })
                    });

                    // Unsubscribe from push
                    await subscription.unsubscribe();
                    console.log('Unsubscribed from push notifications');
                }

                // Clear local storage
                localStorage.removeItem('notification-batch');
                localStorage.removeItem('notification-endpoint');

                // Update UI
                if (enableBtn && batchSelect && statusText) {
                    enableBtn.style.display = 'block';
                    disableBtn.style.display = 'none';
                    statusText.textContent = 'Choose your batch to get started';
                    batchSelect.value = '';
                }

                disableBtn.disabled = false;
                disableBtn.innerHTML = '<i class="bi bi-bell-slash me-1"></i> Disable Alerts';

                showLocalNotification('📵 Alerts Disabled', 'You can re-enable them anytime');

            } catch (error) {
                console.error('Error disabling notifications:', error);
                alert('Failed to disable notifications. Please try again.');

                disableBtn.disabled = false;
                disableBtn.innerHTML = '<i class="bi bi-bell-slash me-1"></i> Disable Alerts';
            }
        });
    }
});

// Helper function to convert VAPID key from base64 to Uint8Array
function urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
    const rawData = window.atob(base64);
    const buffer = new Uint8Array(rawData.length);
    for (let i = 0; i < rawData.length; ++i) {
        buffer[i] = rawData.charCodeAt(i);
    }
    return buffer;
}

// Local notification for immediate feedback
function showLocalNotification(title, body) {
    if (Notification.permission === 'granted') {
        try {
            new Notification(title, {
                body: body,
                icon: '/static/images/logo.png',
                badge: '/static/images/logo.png',
                tag: 'job-alert-config',
                requireInteraction: false
            });
        } catch (error) {
            console.error('Error showing local notification:', error);
        }
    }
}