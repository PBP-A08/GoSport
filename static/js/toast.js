function showToast(type = 'normal', message = '', duration = 3000) {
    const toastComponent = document.getElementById('toast-component');
    const toastTitle = document.getElementById('toast-title');
    const toastMessage = document.getElementById('toast-message');
    const toastIcon = document.getElementById('toast-icon');

    if (!toastComponent) return;

    // Reset semua class dan border
    toastComponent.classList.remove(
        'bg-red-50', 'border-red-500', 'text-red-600',
        'bg-green-50', 'border-green-500', 'text-green-600',
        'bg-blue-50', 'border-blue-500', 'text-blue-600',
        'bg-white', 'border-gray-300', 'text-gray-800'
    );
    toastComponent.style.border = '';

    // Atur gaya dan teks berdasarkan tipe
    if (type.includes('success')) {
        toastComponent.classList.add('bg-green-50', 'border-green-500', 'text-green-600');
        toastComponent.style.border = '1px solid #22c55e';
        toastTitle.textContent = 'Berhasil!';
        toastIcon.textContent = '✅';
    } else if (type.includes('error')) {
        toastComponent.classList.add('bg-red-50', 'border-red-500', 'text-red-600');
        toastComponent.style.border = '1px solid #ef4444';
        toastTitle.textContent = 'Gagal!';
        toastIcon.textContent = '❌';
    } else {
        toastComponent.classList.add('bg-blue-50', 'border-blue-500', 'text-blue-600');
        toastComponent.style.border = '1px solid #3b82f6';
        toastTitle.textContent = 'Info';
        toastIcon.textContent = 'ℹ️';
    }

    toastMessage.textContent = message;

    // Animasi muncul
    toastComponent.classList.remove('opacity-0', 'translate-y-64');
    toastComponent.classList.add('opacity-100', 'translate-y-0');

    // Animasi hilang setelah durasi tertentu
    setTimeout(() => {
        toastComponent.classList.remove('opacity-100', 'translate-y-0');
        toastComponent.classList.add('opacity-0', 'translate-y-64');
    }, duration);
}
