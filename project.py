#!/usr/bin/env python2.7
from flask import Flask, render_template
from flask import request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Competetion, Player, User, Team
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

# Connect to Database and create database session
engine = create_engine('sqlite:///footballinfo.db',
                       connect_args={'check_same_thread': False})
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)

# Functions


def createUser(login_session):
    newUser = User(
        name=login_session['username'],
        email=login_session['email'],
        picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserId(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except BaseException:
        return None

# Facebook connect


@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data

    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (  # noqa
        app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.8/me"

    token = result.split(',')[0].split(':')[1].replace('"', '')

    url = 'https://graph.facebook.com/v2.8/me?access_token=%s&fields=name,id,email' % token  # noqa
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]
    login_session['access_token'] = token

    # Get user picture
    url = 'https://graph.facebook.com/v2.8/me/picture?access_token=%s&redirect=0&height=200&width=200' % token  # noqa
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
    user_id = getUserId(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 100px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '  # noqa
    output += '<script> </script>'
    flash("Now logged in as %s" % login_session['username'])
    return output


# Facebook disconnect
@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (
        facebook_id, access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    competetion = session.query(Competetion).order_by(asc(Competetion.name))
    return render_template('publiccompetetions.html', competetions=competetion)

# JSON APIs to view Player Information


@app.route('/team/<int:team_id>/player/JSON')
def teamplayerJSON(team_id):
    players = session.query(Player).filter_by(team_id=team_id).all()
    return jsonify(players=[i.serialize for i in players])


@app.route('/competetion/<int:competetion_id>/team/JSON')
def teamJSON(competetion_id):
    teams = session.query(Team).filter_by(competetion_id=competetion_id).all()
    return jsonify(teams=[r.serialize for r in teams])


@app.route('/competetion/JSON')
def competetionJSON():
    competetions = session.query(Competetion).all()
    return jsonify(competetions=[r.serialize for r in competetions])

# Show all Competetions


@app.route('/')
@app.route('/competetion/')
def showCompetetion():
    competetions = session.query(Competetion).order_by(asc(Competetion.name))
    if 'username' in login_session:
        return render_template('Competetions.html', competetions=competetions)
    else:
        return render_template(
            'publiccompetetions.html',
            competetions=competetions)


# Create a new Competetion
@app.route('/competetion/new/', methods=['GET', 'POST'])
def newCompetetion():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST' and 'username' in login_session:
        newCompetetion = Competetion(
            name=request.form['name'], user_id=login_session['user_id'])
        session.add(newCompetetion)
        flash('New Competetion %s Successfully Created' % newCompetetion.name)
        session.commit()
        return redirect(url_for('showCompetetion'))
    else:
        return render_template('newCompetetion.html')

# Edit a Competetion


@app.route('/competetion/<int:competetion_id>/edit/', methods=['GET', 'POST'])
def editCompetetion(competetion_id):
    editedCompetetion = session.query(
        Competetion).filter_by(id=competetion_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST' and \
            login_session['user_id'] == editedCompetetion.user_id:
        if request.form['name']:
            editedCompetetion.name = request.form['name']
            flash('Competetion Successfully Edited %s' %
                  editedCompetetion.name)
            return redirect(url_for('showCompetetion'))
    else:
        if login_session['user_id'] == editedCompetetion.user_id:
            return render_template(
                'editCompetetion.html',
                competetion=editedCompetetion)
        else:
            flash("It needs the creator of the page to edit/delete it.")
            return redirect(url_for('showCompetetion'))


# Delete a Competetion
@app.route(
    '/competetion/<int:competetion_id>/delete/',
    methods=[
        'GET',
        'POST'])
def deleteCompetetion(competetion_id):
    if 'username' not in login_session:
        return redirect('/login')
    CompetetionDelete = session.query(
        Competetion).filter_by(id=competetion_id).one()
    if request.method == 'POST' and \
            login_session['user_id'] == CompetetionDelete.user_id:
        session.delete(CompetetionDelete)
        flash('%s Successfully Deleted' % CompetetionDelete.name)
        session.commit()
        return redirect(url_for('showCompetetion'))
    else:
        if login_session['user_id'] == CompetetionDelete.user_id:
            return render_template(
                'deleteCompetetion.html',
                competetion=CompetetionDelete)
        else:
            flash("It needs the creator of the page to edit/delete it.")
            return redirect(url_for('showCompetetion'))

# Show all Teams


@app.route('/')
@app.route('/team/<string:competetion_name>/<int:competetion_id>')
def showTeam(competetion_id, competetion_name):
    competetion_name = competetion_name
    competetion_id = competetion_id
    teams = session.query(Team).filter_by(competetion_id=competetion_id)
    if 'username' in login_session:
        return render_template(
            'Teams.html',
            competetion_id=competetion_id,
            teams=teams,
            competetion_name=competetion_name)
    else:
        return render_template(
            'publicteams.html',
            competetion_id=competetion_id,
            teams=teams,
            competetion_name=competetion_name)


# Create a new Team
@app.route('/team/<int:competetion_id>/new/', methods=['GET', 'POST'])
def newTeam(competetion_id):
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST' and 'username' in login_session:
        newTeam = Team(
            name=request.form['name'],
            competetion_id=competetion_id,
            user_id=login_session['user_id'])
        session.add(newTeam)
        flash('New Team %s Successfully Created' % newTeam.name)
        session.commit()
        return redirect(url_for('showCompetetion'))
    else:
        return render_template('newTeam.html', competetion_id=competetion_id)

# Edit a Team


@app.route(
    '/team/<int:team_id>/<string:team_name>/edit/',
    methods=[
        'GET',
        'POST'])
def editTeam(team_id, team_name):
    if 'username' not in login_session:
        return redirect('/login')
    editedTeam = session.query(Team).filter_by(id=team_id).one()
    if request.method == 'POST' and \
            login_session['user_id'] == editedTeam.user_id:
        if request.form['name']:
            editedTeam.name = request.form['name']
            flash('Team Successfully Edited %s' % editedTeam.name)
            return redirect(url_for('showCompetetion'))
    else:
        if login_session['user_id'] == editedTeam.user_id:
            return render_template(
                'editTeam.html',
                team_id=editedTeam.id,
                team_name=editedTeam.name)
        else:
            flash("It needs the creator of the page to edit/delete it.")
            return redirect(url_for('showCompetetion'))


# Delete a Team
@app.route(
    '/team/<int:team_id>/<string:team_name>/delete/',
    methods=[
        'GET',
        'POST'])
def deleteTeam(team_id, team_name):
    if 'username' not in login_session:
        return redirect('/login')
    deletedTeam = session.query(Team).filter_by(id=team_id).one()
    if request.method == 'POST' and \
            login_session['user_id'] == deletedTeam.user_id:
        session.delete(deletedTeam)
        flash('%s Successfully Deleted' % deletedTeam.name)
        session.commit()
        return redirect(url_for('showCompetetion'))
    else:
        if login_session['user_id'] == deletedTeam.user_id:
            return render_template(
                'deleteTeam.html',
                team_id=deletedTeam.id,
                team_name=deletedTeam.name)

        else:
            flash("It needs the creator of the page to edit/delete it.")
            return redirect(url_for('showCompetetion'))

# Show a Team Player


@app.route('/team/<int:team_id>/')
@app.route('/team/<int:team_id>/Player/')
def showPlayer(team_id):
    team = session.query(Team).filter_by(id=team_id).one()
    players = session.query(Player).filter_by(team_id=team_id).all()
    if 'username' not in login_session:
        return render_template(
            'publicplayers.html',
            players=players,
            team=team)
    else:
        userEmail = session.query(User).filter_by(id=team.user_id).one()
        creator = getUserInfo(team.user_id)
        if userEmail.email != login_session['email']:
            return render_template(
                'publicplayers.html',
                players=players,
                team=team)
        return render_template('Players.html', players=players, team=team)


# Create a new Player
@app.route('/team/<int:team_id>/Player/new/', methods=['GET', 'POST'])
def newPlayer(team_id):
    teamUserId = session.query(Team).filter_by(team_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST' and 'username' in login_session and \
            login_session['user_id'] == teamUserId.user_id:
        newPlayer = Player(
            name=request.form['name'],
            position=request.form['pos'],
            number=request.form['jerseynumber'],
            dob=request.form['dob'],
            nationality=request.form['nationality'],
            contract=request.form['contract'],
            marketvalue=request.form['value'],
            team_id=team_id,
            user_id=login_session['user_id'])
        session.add(newPlayer)
        session.commit()
        flash('New Player %s Successfully Created' % (newPlayer.name))
        return redirect(url_for('showCompetetion'))
    else:
        return render_template('newPlayeritem.html', team_id=team_id)

# Edit a Player


@app.route('/team/player/<int:player_id>/edit', methods=['GET', 'POST'])
def editPlayer(player_id):
    if 'username' not in login_session:
        return redirect('/login')
    editedPlayer = session.query(Player).filter_by(id=player_id).one()
    if request.method == 'POST' and \
            login_session['user_id'] == editedPlayer.user_id:
        if request.form['name']:
            editedPlayer.name = request.form['name']
        if request.form['pos']:
            editedPlayer.position = request.form['pos']
        if request.form['number']:
            editedPlayer.number = request.form['number']
        if request.form['dob']:
            editedPlayer.dob = request.form['dob']
        if request.form['nationality']:
            editedPlayer.nationality = request.form['nationality']
        if request.form['contract']:
            editedPlayer.contract = request.form['contract']
        if request.form['value']:
            editedPlayer.marketvalue = request.form['value']
        session.add(editedPlayer)
        session.commit()
        flash('Player Item Successfully Edited')
        return redirect(url_for('showCompetetion'))
    else:
        if login_session['user_id'] == editedPlayer.user_id:
            return render_template('editPlayeritem.html', player=editedPlayer)
        else:
            flash("It needs the creator of the page to edit/delete it.")
            return redirect(url_for('showCompetetion'))


# Delete a Player
@app.route('/team/player/<int:player_id>/delete', methods=['GET', 'POST'])
def deletePlayer(player_id):
    if 'username' not in login_session:
        return redirect('/login')
    playerDeleted = session.query(Player).filter_by(id=player_id).one()
    if request.method == 'POST'and \
            login_session['user_id'] == deletedTeam.user_id:
        session.delete(playerDeleted)
        session.commit()
        flash('Player Item Successfully Deleted')
        return redirect(url_for('showCompetetion'))
    else:
        if login_session['user_id'] == playerDeleted.user_id:
            return render_template(
                'deletePlayerItem.html',
                player=playerDeleted)
        else:
            flash("It needs the creator of the page to edit/delete it.")
            return redirect(url_for('showCompetetion'))


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000, ssl_context='adhoc')
