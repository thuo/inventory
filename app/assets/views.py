from flask import render_template, flash, redirect, url_for
from flask_login import current_user

import app
from app.assets import assets
from forms import AddAssetForm, AssignAssetForm


@assets.route('/')
def index():
    if current_user.has_admin:
        viewable_assets = app.models.Asset.query.all()
        heading = 'All Assets'
    else:
        viewable_assets = current_user.assets_assigned
        heading = 'Assigned Assets'
    return render_template('assets/index.html', assets=viewable_assets,
                           heading=heading)


@assets.route('/add', methods=['GET', 'POST'])
def add():
    if not current_user.has_admin:
        return render_template('errors/generic.html',
                               message="Only admins can add assets")

    form = AddAssetForm()
    if form.validate_on_submit():
        asset = app.models.Asset(
            form.name.data,
            form.type.data,
            form.description.data,
            form.serial_no.data,
            form.code.data,
            form.purchased.data,
            current_user
        )
        app.db.session.add(asset)
        app.db.session.commit()
        flash("Asset added", "success")
        return redirect(url_for('assets.index'))

    return render_template('assets/add.html', form=form, heading='Add asset')


@assets.route('/<asset_id>/assign', methods=['GET', 'POST'])
def assign(asset_id):
    if not current_user.has_admin:
        return render_template('errors/generic.html',
                               message="Only admins can assign assets")

    asset = app.models.Asset.query.filter_by(id=asset_id).first_or_404()
    if asset.is_assigned:
        return render_template('errors/generic.html',
                               message="This asset is already assigned to %s"
                                       % asset.assignee.name)

    form = AssignAssetForm()
    form.user.choices = [(user.id, "%s &lt;%s&gt;" % (user.name, user.email))
                         for user in app.models.User.query.all()
                         if user.is_staff]

    if form.validate_on_submit():
        user = app.models.User.query.filter_by(id=form.user.data).first()
        if user is not None:
            asset.assign(user, form.return_date.data)
            app.db.session.add_all([asset, user])
            app.db.session.commit()
            flash("Asset assigned to %s" % user.name, "success")
            return redirect(url_for('assets.index'))

        flash("You must select a user to assign", "danger")

    return render_template('assets/assign.html', form=form,
                       heading='Assign asset', asset=asset)


@assets.route('/<asset_id>/reclaim')
def reclaim(asset_id):
    if not current_user.has_admin:
        return render_template('errors/generic.html',
                               message="Only admins can reclaim assets")

    asset = app.models.Asset.query.filter_by(id=asset_id).first_or_404()
    # copy the name 'cause assignee will be removed
    name = asset.assignee.name[:]
    asset.reclaim()
    app.db.session.add(asset)
    app.db.session.commit()

    flash("Asset reclaimed from %s" % name, "success")
    return redirect(url_for('assets.index'))
