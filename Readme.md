# Item Catalog Project

The Item Catalog Project presents a list of:
1- Leagues or Competetions
2- Teams on those Leagues
3- Players on those teams

## Prepare the software and data

1- Install Vagrant and VirtualBox if you have not done so already. 
you can find them here with instructions on how to install them:
Vagrant : https://www.vagrantup.com/
Virtualbox : https://www.virtualbox.org/

2- Clone the fullstack-nanodegree-vm repository. There is a catalog folder provided for you, but no files have been included. If a catalog folder does not exist, simply create your own inside of the vagrant folder, you can find it here : https://github.com/udacity/fullstack-nanodegree-vm

3- Launch the Vagrant VM (by typing vagrant up in the directory fullstack/vagrant from the terminal). You can find further instructions on how to do so here.

4- Run your application within the VM by typing python /vagrant/catalog/project.py into the Terminal.

5- Access and test the application by visiting https://localhost:5000/login locally on your browser.

## Modules:
It consists of only 1 module **project.py**.

### project.py
This module contains all the methods that have been used in this project let's take a sample to those methods and routes :

`@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)`
this route takes us to the login page , from which you can sign in to the service via Facebook or you can continue without signing in however you'll have limited access through the website , ofcourse you have to have a Facebook account.

##### JSON endpoint:
The first one :

`@app.route('/team/<int:team_id>/player/JSON')
def teamplayerJSON(team_id):
    players = session.query(Player).filter_by(team_id=team_id).all()
    return jsonify(players=[i.serialize for i in players])`
It returns all the players details in the database , you have to provide it with the team id , you can get it from the next end point.

The Second:
`@app.route('/competetion/<int:competetion_id>/team/JSON')
def teamJSON(competetion_id):
    teams = session.query(Team).filter_by(competetion_id=competetion_id).all()
    return jsonify(teams=[r.serialize for r in teams])`
It returns all the teams details in the database , you have to provide it with the competetion id , you can get it from the following end point.

The Third:
`@app.route('/competetion/JSON')
def competetionJSON():
    competetions = session.query(Competetion).all()
    return jsonify(competetions=[r.serialize for r in competetions])`
It returns all the competetions details from the database.

##### Database:
The database consists of 4 tables :
1- User
2- Competetion
3- Team
4- Player

Lets start with : 1- User:
it has the following tables :
a- id
b- name 
c- email
d- picture

2- Competetion :
a- id
b- name
c- user_id FK to the users id that created the Competetion

3- Team:
a- id
b- name
c- competetion_id FK to the Competetion of this team
d- user_id FK to the creator of this team

4- Player:
a- id
b- name
c- position
d- number
e- dob //Date of birth
f- nationality
g- contract // when will his contract finish
h- marketvalue
i- team_id FK to the team of the player
j- user_id FK to the creator of the player

and You'll find the serialize of each of those tables (except the user ofcourse).


##To run the project YOU'll NEED TO RUN THIS FILE WITH PYTHON2.7.
It only initiates the routes and methods in the **project.py** file.
