// Service Worker for Push Notifications
// Version 1.0

console.log('Service Worker loaded');

// Install event
self.addEventListener('install', function(event) {
    console.log('Service Worker installing...');
    self.skipWaiting();
});

// Activate event
self.addEventListener('activate', function(event) {
    console.log('Service Worker activating...');
    event.waitUntil(clients.claim());
});

// Push event - receives notifications
self.addEventListener('push', function(event) {
    console.log('Push notification received', event);

    if (event.data) {
        const data = event.data.json();
        console.log('Push data:', data);

        const options = {
            body: data.body,
            icon: data.icon || '/static/images/logo.png',
            badge: data.badge || '/static/images/logo.png',
            vibrate: [200, 100, 200],
            tag: data.tag || 'default',
            requireInteraction: data.requireInteraction || false,
            data: {
                url: data.url || '/',
                jobData: data.data || {}
            },
            actions: [
                {
                    action: 'view',
                    title: '👀 View Job',
                    icon: '/static/images/logo.png'
                },
                {
                    action: 'close',
                    title: '✖ Close',
                    icon: '/static/images/logo.png'
                }
            ]
        };

        event.waitUntil(
            self.registration.showNotification(data.title, options)
        );
    }
});

// Notification click event
self.addEventListener('notificationclick', function(event) {
    console.log('Notification clicked:', event.action);

    event.notification.close();

    if (event.action === 'view' || !event.action) {
        const urlToOpen = event.notification.data.url;

        event.waitUntil(
            clients.matchAll({
                type: 'window',
                includeUncontrolled: true
            })
            .then(function(clientList) {
                // Check if there's already a window open
                for (let i = 0; i < clientList.length; i++) {
                    const client = clientList[i];
                    if (client.url === urlToOpen && 'focus' in client) {
                        return client.focus();
                    }
                }
                // If not, open a new window
                if (clients.openWindow) {
                    return clients.openWindow(urlToOpen);
                }
            })
        );
    }
});

// Notification close event
self.addEventListener('notificationclose', function(event) {
    console.log('Notification closed:', event.notification.tag);
});