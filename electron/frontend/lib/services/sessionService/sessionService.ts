export const createEventSource = (url) => {
    const eventSource = new EventSource(url);

    return {
        onMessage: (callback) => eventSource.onmessage = (event) => callback(event),
        onError: (callback) => eventSource.onerror = (event) => callback(event),
        close: () => eventSource.close(),
    };
};
