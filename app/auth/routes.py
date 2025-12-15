"""
Routes d'authentification : login, logout, inscription.
"""

from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from datetime import datetime

from app.auth import bp
from app.models.user import User, Role
from app.extensions import db
from app.auth.decorators import admin_required


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Page de connexion."""
    if current_user.is_authenticated:
        return redirect(url_for('home.index'))
    
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = data.get('username', '').strip()
        password = data.get('password', '')
        remember = data.get('remember', False)
        
        if not username or not password:
            error_msg = 'Nom d\'utilisateur et mot de passe requis.'
            if request.is_json:
                return jsonify({'success': False, 'message': error_msg}), 400
            flash(error_msg, 'error')
            return render_template('auth/login.html'), 400
        
        # Rechercher l'utilisateur
        user = User.query.filter_by(username=username).first()
        
        if not user:
            # Ne pas révéler que l'utilisateur n'existe pas (sécurité)
            error_msg = 'Nom d\'utilisateur ou mot de passe incorrect.'
            if request.is_json:
                return jsonify({'success': False, 'message': error_msg}), 401
            flash(error_msg, 'error')
            return render_template('auth/login.html'), 401
        
        # Vérifier si le compte est verrouillé
        if user.is_locked():
            error_msg = 'Compte verrouillé. Veuillez réessayer plus tard.'
            if request.is_json:
                return jsonify({'success': False, 'message': error_msg}), 423
            flash(error_msg, 'error')
            return render_template('auth/login.html'), 423
        
        # Vérifier si le compte est actif
        if not user.is_active:
            error_msg = 'Compte désactivé. Contactez un administrateur.'
            if request.is_json:
                return jsonify({'success': False, 'message': error_msg}), 403
            flash(error_msg, 'error')
            return render_template('auth/login.html'), 403
        
        # Vérifier le mot de passe
        if not user.check_password(password):
            user.record_failed_login()
            error_msg = 'Nom d\'utilisateur ou mot de passe incorrect.'
            if request.is_json:
                return jsonify({'success': False, 'message': error_msg}), 401
            flash(error_msg, 'error')
            return render_template('auth/login.html'), 401
        
        # Connexion réussie
        login_user(user, remember=remember)
        user.record_login()
        current_app.logger.info(f"User {user.username} logged in successfully")
        
        if request.is_json:
            return jsonify({
                'success': True,
                'message': 'Connexion réussie',
                'user': user.to_dict()
            })
        
        # Redirection après connexion
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        return redirect(url_for('home.index'))
    
    return render_template('auth/login.html')


@bp.route('/logout')
@login_required
def logout():
    """Déconnexion de l'utilisateur."""
    username = current_user.username
    logout_user()
    current_app.logger.info(f"User {username} logged out")
    flash('Vous avez été déconnecté avec succès.', 'info')
    
    if request.is_json:
        return jsonify({'success': True, 'message': 'Déconnexion réussie'})
    
    return redirect(url_for('auth.login'))


@bp.route('/register', methods=['GET', 'POST'])
def register():
    """Page d'inscription (limitée en production)."""
    # En production, désactiver l'inscription publique si nécessaire
    if current_app.config.get('DISABLE_PUBLIC_REGISTRATION', False):
        flash('L\'inscription publique est désactivée.', 'error')
        return redirect(url_for('auth.login'))
    
    if current_user.is_authenticated:
        return redirect(url_for('home.index'))
    
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = data.get('username', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        confirm_password = data.get('confirm_password', '')
        
        # Validation
        errors = []
        
        if not username or len(username) < 3:
            errors.append('Le nom d\'utilisateur doit contenir au moins 3 caractères.')
        elif User.query.filter_by(username=username).first():
            errors.append('Ce nom d\'utilisateur est déjà pris.')
        
        if not email or '@' not in email:
            errors.append('Email invalide.')
        elif User.query.filter_by(email=email).first():
            errors.append('Cet email est déjà utilisé.')
        
        if not password or len(password) < 8:
            errors.append('Le mot de passe doit contenir au moins 8 caractères.')
        elif password != confirm_password:
            errors.append('Les mots de passe ne correspondent pas.')
        
        if errors:
            if request.is_json:
                return jsonify({'success': False, 'errors': errors}), 400
            for error in errors:
                flash(error, 'error')
            return render_template('auth/register.html'), 400
        
        # Créer l'utilisateur
        user = User(
            username=username,
            email=email,
            role=Role.USER,
            is_active=True
        )
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            current_app.logger.info(f"New user registered: {username}")
            
            if request.is_json:
                return jsonify({
                    'success': True,
                    'message': 'Inscription réussie. Vous pouvez maintenant vous connecter.'
                }), 201
            
            flash('Inscription réussie. Vous pouvez maintenant vous connecter.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error registering user: {e}")
            error_msg = 'Erreur lors de l\'inscription. Veuillez réessayer.'
            if request.is_json:
                return jsonify({'success': False, 'message': error_msg}), 500
            flash(error_msg, 'error')
            return render_template('auth/register.html'), 500
    
    return render_template('auth/register.html')


@bp.route('/profile')
@login_required
def profile():
    """Page de profil utilisateur."""
    if request.is_json:
        return jsonify({'success': True, 'user': current_user.to_dict()})
    return render_template('auth/profile.html', user=current_user)


@bp.route('/users')
@admin_required
def list_users():
    """Liste des utilisateurs (admin uniquement)."""
    users = User.query.order_by(User.created_at.desc()).all()
    
    if request.is_json:
        return jsonify({
            'success': True,
            'users': [user.to_dict() for user in users]
        })
    
    return render_template('auth/users.html', users=users)

