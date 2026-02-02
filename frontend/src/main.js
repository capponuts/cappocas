/**
 * Cappocas - Application Frontend
 * Automatisation de postage d'annonces
 */

// ===================
// API Client
// ===================
const API_BASE = '/api';

class ApiClient {
    constructor() {
        this.token = localStorage.getItem('token');
    }

    setToken(token) {
        this.token = token;
        localStorage.setItem('token', token);
    }

    clearToken() {
        this.token = null;
        localStorage.removeItem('token');
    }

    async request(endpoint, options = {}) {
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers,
        };

        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }

        const response = await fetch(`${API_BASE}${endpoint}`, {
            ...options,
            headers,
        });

        if (response.status === 401) {
            this.clearToken();
            app.showPage('login');
            throw new Error('Session expirée');
        }

        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || 'Une erreur est survenue');
        }

        if (response.status === 204) {
            return null;
        }

        return response.json();
    }

    // Auth
    async login(email, password) {
        const data = await this.request('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password }),
        });
        this.setToken(data.access_token);
        return data;
    }

    async register(username, email, password, telegramChatId = null) {
        const data = await this.request('/auth/register', {
            method: 'POST',
            body: JSON.stringify({
                username,
                email,
                password,
                telegram_chat_id: telegramChatId,
            }),
        });
        this.setToken(data.access_token);
        return data;
    }

    async getMe() {
        return this.request('/auth/me');
    }

    // Listings
    async getListings() {
        return this.request('/listings/');
    }

    async getListing(id) {
        return this.request(`/listings/${id}`);
    }

    async createListing(data) {
        return this.request('/listings/', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async updateListing(id, data) {
        return this.request(`/listings/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    }

    async deleteListing(id) {
        return this.request(`/listings/${id}`, { method: 'DELETE' });
    }

    async publishListing(id) {
        return this.request(`/listings/${id}/publish`, { method: 'POST' });
    }

    // Categories (Vinted)
    async analyzeCategory(title, description = '') {
        return this.request('/categories/analyze', {
            method: 'POST',
            body: JSON.stringify({ title, description }),
        });
    }

    async searchCategories(query) {
        return this.request(`/categories/search?q=${encodeURIComponent(query)}`);
    }

    // Uploads
    async uploadImages(files) {
        const formData = new FormData();
        files.forEach(file => formData.append('files', file));

        const response = await fetch(`${API_BASE}/uploads/images`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.token}`,
            },
            body: formData,
        });

        if (!response.ok) {
            throw new Error('Erreur lors de l\'upload');
        }

        return response.json();
    }
}

const api = new ApiClient();

// ===================
// App State & Router
// ===================
class App {
    constructor() {
        this.currentPage = 'login';
        this.user = null;
        this.listings = [];
        this.uploadedImages = [];
    }

    init() {
        this.setupEventListeners();
        this.checkAuth();
    }

    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const page = e.target.dataset.page;
                this.showPage(page);
            });
        });

        // Auth forms
        document.getElementById('login-form').addEventListener('submit', (e) => this.handleLogin(e));
        document.getElementById('register-form').addEventListener('submit', (e) => this.handleRegister(e));
        document.getElementById('show-register').addEventListener('click', (e) => {
            e.preventDefault();
            this.showPage('register');
        });
        document.getElementById('show-login').addEventListener('click', (e) => {
            e.preventDefault();
            this.showPage('login');
        });

        // Logout
        document.getElementById('logout-btn').addEventListener('click', () => this.handleLogout());

        // Create listing form
        document.getElementById('create-listing-form').addEventListener('submit', (e) => this.handleCreateListing(e));

        // Image upload
        const uploadZone = document.getElementById('upload-zone');
        const imageInput = document.getElementById('image-input');

        uploadZone.addEventListener('click', () => imageInput.click());
        uploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadZone.classList.add('dragover');
        });
        uploadZone.addEventListener('dragleave', () => {
            uploadZone.classList.remove('dragover');
        });
        uploadZone.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadZone.classList.remove('dragover');
            this.handleImageUpload(e.dataTransfer.files);
        });
        imageInput.addEventListener('change', (e) => {
            this.handleImageUpload(e.target.files);
        });

        // New listing button
        document.getElementById('new-listing-btn').addEventListener('click', () => {
            this.showPage('create');
        });

        // Category auto-detection (debounced)
        let categoryDebounceTimer;
        const titleInput = document.getElementById('listing-title');
        const descriptionInput = document.getElementById('listing-description');
        
        const triggerCategoryAnalysis = () => {
            clearTimeout(categoryDebounceTimer);
            categoryDebounceTimer = setTimeout(() => {
                this.analyzeVintedCategory();
            }, 500); // Attendre 500ms après la dernière frappe
        };
        
        titleInput.addEventListener('input', triggerCategoryAnalysis);
        descriptionInput.addEventListener('input', triggerCategoryAnalysis);
    }

    async analyzeVintedCategory() {
        const title = document.getElementById('listing-title').value.trim();
        const description = document.getElementById('listing-description').value.trim();
        const previewEl = document.getElementById('vinted-category-preview');
        
        if (title.length < 3) {
            previewEl.className = 'category-preview';
            previewEl.innerHTML = '<span class="category-hint">💡 La catégorie sera détectée automatiquement d\'après le titre</span>';
            return;
        }
        
        // Afficher loading
        previewEl.className = 'category-preview loading';
        previewEl.innerHTML = '<span class="category-hint">🔍 Analyse en cours...</span>';
        
        try {
            const result = await api.analyzeCategory(title, description);
            
            if (result.suggested_category) {
                const confidence = result.confidence;
                let confidenceClass = 'confidence-low';
                let confidenceText = 'Faible';
                
                if (confidence >= 0.7) {
                    confidenceClass = 'confidence-high';
                    confidenceText = 'Élevée';
                } else if (confidence >= 0.4) {
                    confidenceClass = 'confidence-medium';
                    confidenceText = 'Moyenne';
                }
                
                let html = `
                    <div class="category-detected">
                        <div class="category-path">${result.suggested_category.full_path}</div>
                        <div class="category-confidence ${confidenceClass}">
                            Confiance: ${confidenceText} (${Math.round(confidence * 100)}%)
                            ${result.detected_gender ? ` • Genre détecté: ${result.detected_gender}` : ''}
                        </div>
                `;
                
                if (result.alternatives && result.alternatives.length > 0) {
                    html += `
                        <div class="category-alternatives">
                            Alternatives: ${result.alternatives.map(a => `<span>${a.name}</span>`).join('')}
                        </div>
                    `;
                }
                
                html += '</div>';
                
                previewEl.className = 'category-preview detected';
                previewEl.innerHTML = html;
                
                // Stocker la catégorie détectée
                this.detectedCategory = result.suggested_category;
            } else {
                previewEl.className = 'category-preview';
                previewEl.innerHTML = `<span class="category-hint">⚠️ ${result.message || 'Impossible de détecter la catégorie'}</span>`;
                this.detectedCategory = null;
            }
        } catch (error) {
            previewEl.className = 'category-preview';
            previewEl.innerHTML = '<span class="category-hint">❌ Erreur lors de l\'analyse</span>';
            this.detectedCategory = null;
        }
    }

    async checkAuth() {
        if (!api.token) {
            this.showPage('login');
            return;
        }

        try {
            this.user = await api.getMe();
            this.showPage('dashboard');
        } catch (error) {
            this.showPage('login');
        }
    }

    showPage(page) {
        // Masquer toutes les pages
        document.querySelectorAll('.page').forEach(p => p.style.display = 'none');

        // Afficher la page demandée
        const pageEl = document.getElementById(`page-${page}`);
        if (pageEl) {
            pageEl.style.display = 'block';
        }

        // Mettre à jour la navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.toggle('active', link.dataset.page === page);
        });

        // Afficher/masquer le bouton de déconnexion
        const logoutBtn = document.getElementById('logout-btn');
        const nav = document.getElementById('nav');
        const isAuth = ['login', 'register'].includes(page);
        logoutBtn.style.display = isAuth ? 'none' : 'block';
        nav.style.display = isAuth ? 'none' : 'flex';

        // Charger les données si nécessaire
        if (page === 'dashboard') {
            this.loadDashboard();
        } else if (page === 'listings') {
            this.loadListings();
        }

        this.currentPage = page;
    }

    // ===================
    // Auth Handlers
    // ===================
    async handleLogin(e) {
        e.preventDefault();
        const email = document.getElementById('login-email').value;
        const password = document.getElementById('login-password').value;

        try {
            const data = await api.login(email, password);
            this.user = data.user;
            this.showToast('Connexion réussie', 'success');
            this.showPage('dashboard');
        } catch (error) {
            this.showToast(error.message, 'error');
        }
    }

    async handleRegister(e) {
        e.preventDefault();
        const username = document.getElementById('register-username').value;
        const email = document.getElementById('register-email').value;
        const password = document.getElementById('register-password').value;
        const telegram = document.getElementById('register-telegram').value;

        try {
            const data = await api.register(username, email, password, telegram || null);
            this.user = data.user;
            this.showToast('Compte créé avec succès', 'success');
            this.showPage('dashboard');
        } catch (error) {
            this.showToast(error.message, 'error');
        }
    }

    handleLogout() {
        api.clearToken();
        this.user = null;
        this.showPage('login');
        this.showToast('Déconnexion réussie', 'success');
    }

    // ===================
    // Dashboard
    // ===================
    async loadDashboard() {
        try {
            this.listings = await api.getListings();
            
            // Calculer les stats
            const total = this.listings.length;
            const published = this.listings.filter(l => 
                l.leboncoin_status === 'published' || l.vinted_status === 'published'
            ).length;
            const pending = this.listings.filter(l => 
                l.leboncoin_status === 'pending' || l.vinted_status === 'pending'
            ).length;
            const failed = this.listings.filter(l => 
                l.leboncoin_status === 'failed' || l.vinted_status === 'failed'
            ).length;

            document.getElementById('total-listings').textContent = total;
            document.getElementById('published-listings').textContent = published;
            document.getElementById('pending-listings').textContent = pending;
            document.getElementById('failed-listings').textContent = failed;

            // Activité récente
            const recentActivity = document.getElementById('recent-activity');
            if (this.listings.length > 0) {
                recentActivity.innerHTML = this.listings.slice(0, 5).map(listing => `
                    <div class="activity-item">
                        <span>${this.getStatusEmoji(listing)}</span>
                        <span>${listing.title}</span>
                        <span style="color: var(--text-muted); margin-left: auto;">
                            ${new Date(listing.created_at).toLocaleDateString('fr-FR')}
                        </span>
                    </div>
                `).join('');
            } else {
                recentActivity.innerHTML = '<p class="empty-message">Aucune activité récente</p>';
            }
        } catch (error) {
            this.showToast(error.message, 'error');
        }
    }

    getStatusEmoji(listing) {
        if (listing.leboncoin_status === 'published' || listing.vinted_status === 'published') return '✅';
        if (listing.leboncoin_status === 'pending' || listing.vinted_status === 'pending') return '⏳';
        if (listing.leboncoin_status === 'failed' || listing.vinted_status === 'failed') return '❌';
        return '📝';
    }

    // ===================
    // Listings
    // ===================
    async loadListings() {
        try {
            this.listings = await api.getListings();
            const container = document.getElementById('listings-container');

            if (this.listings.length === 0) {
                container.innerHTML = '<p class="empty-message">Vous n\'avez pas encore d\'annonces</p>';
                return;
            }

            container.innerHTML = this.listings.map(listing => `
                <div class="listing-card" data-id="${listing.id}">
                    <img class="listing-image" src="${listing.images[0]?.url || '/placeholder.png'}" alt="${listing.title}">
                    <div class="listing-info">
                        <h3>${listing.title}</h3>
                        <span class="listing-price">${listing.price.toFixed(2)} €</span>
                        <div class="listing-status">
                            ${listing.post_to_leboncoin ? `<span class="status-badge ${listing.leboncoin_status}">LBC: ${this.translateStatus(listing.leboncoin_status)}</span>` : ''}
                            ${listing.post_to_vinted ? `<span class="status-badge ${listing.vinted_status}">Vinted: ${this.translateStatus(listing.vinted_status)}</span>` : ''}
                        </div>
                    </div>
                    <div class="listing-actions">
                        <button onclick="app.publishListing(${listing.id})" title="Publier">🚀</button>
                        <button onclick="app.deleteListing(${listing.id})" title="Supprimer">🗑️</button>
                    </div>
                </div>
            `).join('');
        } catch (error) {
            this.showToast(error.message, 'error');
        }
    }

    translateStatus(status) {
        const translations = {
            'draft': 'Brouillon',
            'pending': 'En attente',
            'scheduled': 'Planifié',
            'publishing': 'Publication...',
            'published': 'Publié',
            'failed': 'Échec',
            'deleted': 'Supprimé',
        };
        return translations[status] || status;
    }

    async publishListing(id) {
        try {
            await api.publishListing(id);
            this.showToast('Publication lancée', 'success');
            this.loadListings();
        } catch (error) {
            this.showToast(error.message, 'error');
        }
    }

    async deleteListing(id) {
        if (!confirm('Êtes-vous sûr de vouloir supprimer cette annonce ?')) {
            return;
        }

        try {
            await api.deleteListing(id);
            this.showToast('Annonce supprimée', 'success');
            this.loadListings();
        } catch (error) {
            this.showToast(error.message, 'error');
        }
    }

    // ===================
    // Create Listing
    // ===================
    async handleImageUpload(files) {
        const validFiles = Array.from(files).filter(file => 
            ['image/jpeg', 'image/png', 'image/webp', 'image/gif'].includes(file.type)
        );

        if (validFiles.length === 0) {
            this.showToast('Aucun fichier image valide', 'error');
            return;
        }

        try {
            const uploaded = await api.uploadImages(validFiles);
            this.uploadedImages.push(...uploaded);
            this.renderImagePreviews();
            this.showToast(`${uploaded.length} image(s) uploadée(s)`, 'success');
        } catch (error) {
            this.showToast(error.message, 'error');
        }
    }

    renderImagePreviews() {
        const container = document.getElementById('image-preview');
        container.innerHTML = this.uploadedImages.map((img, index) => `
            <div class="image-preview">
                <img src="${img.url}" alt="Preview">
                <button class="remove-btn" onclick="app.removeImage(${index})">×</button>
            </div>
        `).join('');
    }

    removeImage(index) {
        this.uploadedImages.splice(index, 1);
        this.renderImagePreviews();
    }

    async handleCreateListing(e) {
        e.preventDefault();

        // Récupérer les couleurs (séparées par virgule)
        const colorsValue = document.getElementById('listing-colors').value;
        const colors = colorsValue ? colorsValue.split(',').map(c => c.trim()).filter(c => c) : null;

        const data = {
            title: document.getElementById('listing-title').value,
            description: document.getElementById('listing-description').value,
            price: parseFloat(document.getElementById('listing-price').value),
            condition: document.getElementById('listing-condition').value || null,
            // Catégorie auto-détectée (stockée dans this.detectedCategory)
            category: this.detectedCategory?.name || null,
            category_path: this.detectedCategory?.path || null,
            location: document.getElementById('listing-location').value || null,
            // Nouveaux champs Vinted
            brand: document.getElementById('listing-brand').value || null,
            size: document.getElementById('listing-size').value || null,
            colors: colors,
            // Plateformes
            post_to_leboncoin: document.getElementById('post-leboncoin').checked,
            post_to_vinted: document.getElementById('post-vinted').checked,
            image_ids: this.uploadedImages.map(img => img.id),
        };

        const scheduleValue = document.getElementById('listing-schedule').value;
        if (scheduleValue) {
            data.scheduled_at = new Date(scheduleValue).toISOString();
        }

        // Vérifier qu'une catégorie a été détectée pour Vinted
        if (data.post_to_vinted && !this.detectedCategory) {
            this.showToast('Impossible de détecter la catégorie Vinted. Veuillez préciser le titre.', 'warning');
            return;
        }

        try {
            const listing = await api.createListing(data);
            this.showToast('Annonce créée avec succès', 'success');

            // Publier si pas de planification
            if (!scheduleValue) {
                await api.publishListing(listing.id);
                this.showToast('Publication lancée', 'success');
            }

            // Reset form
            e.target.reset();
            this.uploadedImages = [];
            this.detectedCategory = null;
            this.renderImagePreviews();
            
            // Reset category preview
            const previewEl = document.getElementById('vinted-category-preview');
            previewEl.className = 'category-preview';
            previewEl.innerHTML = '<span class="category-hint">💡 La catégorie sera détectée automatiquement d\'après le titre</span>';
            
            this.showPage('listings');
        } catch (error) {
            this.showToast(error.message, 'error');
        }
    }

    // ===================
    // Toast Notifications
    // ===================
    showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <span>${this.getToastIcon(type)}</span>
            <span>${message}</span>
        `;
        container.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = 'slideIn 0.3s ease reverse';
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    }

    getToastIcon(type) {
        const icons = {
            success: '✓',
            error: '✗',
            warning: '⚠',
            info: 'ℹ',
        };
        return icons[type] || icons.info;
    }
}

// ===================
// Initialize
// ===================
const app = new App();
document.addEventListener('DOMContentLoaded', () => app.init());

// Expose app globally for inline handlers
window.app = app;
