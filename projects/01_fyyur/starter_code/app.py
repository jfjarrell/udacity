#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import sys

import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from sqlalchemy import func
from werkzeug.exceptions import abort

from forms import *
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

migrate = Migrate(app, db)

# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String))
    seeking_description = db.Column(db.String(500))
    website = db.Column(db.String(500))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    artist_shows = db.relationship('Shows', backref='artist_show_list', lazy=True, cascade = 'save-update')

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String))
    seeking_description = db.Column(db.String(500))
    website = db.Column(db.String(500))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    venue_shows = db.relationship('Shows', backref='venue_show_list', lazy=True, cascade = 'save-update')


class Shows(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'))
    venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'))
    start_time = db.Column(db.DateTime)

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):

      date = dateutil.parser.parse(value)

      if format == 'full':
          format="EEEE MMMM, d, y 'at' h:mma"
      elif format == 'medium':
          format="EE MM, dd, y h:mma"

      return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.

    data = []

    venues = Venue.query.all()

    places = Venue.query.distinct(Venue.city, Venue.state).all()

    for place in places:
        data.append({
            "city": place.city,
            "state": place.state,
            "venues": [{
                "id": venue.id,
                "name": venue.name,
                "num_upcoming_shows": len(db.session.query(Shows).join(Venue).filter(
            Shows.venue_id == venue.id,
            Shows.start_time > datetime.now()).all())
            } for venue in venues if venue.city == place.city and venue.state == place.state]
            })

    return render_template('pages/venues.html', areas=data);


@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"

    term = request.form.get('search_term')

    venues = Venue.query.filter(func.lower(Venue.name).like(func.lower('%'+term+'%'))).all()


    response={
        "count": len(venues),
        "data": [{
          "id": venue.id,
          "name": venue.name,
          "num_upcoming_shows": len(db.session.query(Shows).join(Venue).filter(
            Shows.venue_id == venue.id,
            Shows.start_time > datetime.now()).all())
            }for venue in venues]
    }

    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):

    venue = Venue.query.get(venue_id)

    past_shows = db.session.query(Artist, Shows).join(Shows).join(Venue).filter(
      Shows.artist_id == Artist.id,
      Shows.venue_id == venue_id,
      Shows.start_time < datetime.now()).all()

    upcoming_shows = db.session.query(Artist, Shows).join(Shows).join(Venue).filter(
      Shows.artist_id == Artist.id,
      Shows.venue_id == venue_id,
      Shows.start_time > datetime.now()).all()

    data = {
      "id": venue.id,
      "name": venue.name,
      "genres": venue.genres,
      "city": venue.city,
      "state": venue.state,
      "phone": venue.phone,
      "seeking_description": venue.seeking_description,
      "image_link": venue.image_link,
      "past_shows": [{
        "artist_id": artist.id,
        "artist_name": artist.name,
        "artist_image_link": artist.image_link,
        "start_time": format_datetime(str(show.start_time))
      } for artist, show in past_shows],
      "upcoming_shows": [{
        "artist_id": artist.id,
        "artist_name": artist.name,
        "artist_image_link": artist.image_link,
        "start_time": format_datetime(str(show.start_time))
      } for artist, show in upcoming_shows],
      "upcoming_shows_count": len(upcoming_shows),
      "past_shows_count": len(past_shows)
    }
    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  error = False

  try:
    name = request.form.get('name')
    city = request.form.get('city')
    state = request.form.get('state')
    address = request.form.get('address')
    phone = request.form.get('phone')
    genres = request.form.getlist('genres')
    facebook_link = request.form.get('facebook_link')
    venue = Venue(name=name, city=city, state=state, address=address, phone=phone, genres=genres, facebook_link=facebook_link)
    db.session.add(venue)
  except():
    db.session.rollback()
    error = True
    print(sys.exc_info())
  finally:
    db.session.commit()
    db.session.close()
  if error:
    abort(500)
    flash('An error occurred. Venue ' + name + ' could not be listed.')
  else:
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
 #   return data
  # on successful db insert, flash success

  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():

    data = (Artist.query.all())
    return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".

    term = request.form.get('search_term')

    artists = Artist.query.filter(func.lower(Artist.name).like(func.lower('%' + term + '%'))).all()

    response = {
      "count": len(artists),
      "data": [{
          "id": artist.id,
          "name": artist.name,
          "num_upcoming_shows": len(db.session.query(Shows).join(Artist).filter(
              Shows.artist_id == artist.id,
              Shows.start_time > datetime.now()).all())
      } for artist in artists]
    }
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):

    artist = Artist.query.get(artist_id)

    past_shows = db.session.query(Venue, Shows).join (Shows).join(Artist).filter(
      Shows.venue_id == Venue.id,
      Shows.artist_id == artist_id,
      Shows.start_time < datetime.now()).all()

    upcoming_shows = db.session.query(Venue, Shows).join (Shows).join(Artist).filter(
      Shows.venue_id == Venue.id,
      Shows.artist_id == artist_id,
      Shows.start_time > datetime.now()).all()

    data = {
      "id": artist.id,
      "name": artist.name,
      "genres": artist.genres,
      "city": artist.city,
      "state": artist.state,
      "phone": artist.phone,
      "seeking_description": artist.seeking_description,
      "image_link": artist.image_link,
      "past_shows": [{
        "venue_id": venue.id,
        "venue_name": venue.name,
        "venue_image_link": venue.image_link,
        "start_time": format_datetime(str(show.start_time))
      }for venue, show in past_shows],
      "upcoming_shows": [{
        "venue_id": venue.id,
        "venue_name": venue.name,
        "venue_image_link": venue.image_link,
        "start_time": format_datetime(str(show.start_time))
      }for venue, show in upcoming_shows],
      "upcoming_shows_count": len(upcoming_shows),
      "past_shows_count": len(past_shows)
    }

  #data = list(filter(lambda d: d['id'] == artist_id, [data1, data2, data3]))[0]
    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist={
    "id": 4,
    "name": "Guns N Petals",
    "genres": ["Rock n Roll"],
    "city": "San Francisco",
    "state": "CA",
    "phone": "326-123-5000",
    "website": "https://www.gunsnpetalsband.com",
    "facebook_link": "https://www.facebook.com/GunsNPetals",
    "seeking_venue": True,
    "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
    "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80"
  }
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue={
    "id": 1,
    "name": "The Musical Hop",
    "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
    "address": "1015 Folsom Street",
    "city": "San Francisco",
    "state": "CA",
    "phone": "123-123-1234",
    "website": "https://www.themusicalhop.com",
    "facebook_link": "https://www.facebook.com/TheMusicalHop",
    "seeking_talent": True,
    "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
    "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60"
  }
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  error = False

  try:
    name = request.form.get('name')
    city = request.form.get('city')
    state = request.form.get('state')
    phone = request.form.get('phone')
    genres = request.form.getlist('genres')
    facebook_link = request.form.get('facebook_link')
    artist = Artist(name=name, city=city, state=state, phone=phone, genres=genres, facebook_link=facebook_link)
    db.session.add(artist)
  except():
    db.session.rollback()
    error = True
    print(sys.exc_info())
  finally:
    db.session.commit()
    db.session.close()
  if error:
    abort(500)
    flash('An error occurred. Artist ' + name + ' could not be listed.')
  else:
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  # on successful db insert, flash success

  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  current_time = datetime.now()

  data = []

  shows = (Shows.query.all())

  for s in shows:
    artist = Artist.query.get(s.artist_id)
    venue = Venue.query.get(s.venue_id)

    if s.start_time > current_time:
      data.append({
        "venue_id": s.venue_id,
        "venue_name": venue.name,
        "artist_id": s.artist_id,
        "artist_name": artist.name,
        "artist_image_link": artist.image_link,
        "start_time": format_datetime(str(s.start_time))

      })
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  error = False

  try:
    artist_id = request.form.get('artist_id')
    venue_id = request.form.get('venue_id')
    start_time = request.form.get('start_time')
    show = Shows(artist_id=artist_id, venue_id=venue_id, start_time=start_time)
    db.session.add(show)
  except():
    db.session.rollback()
    error = True
    print(sys.exc_info())
  finally:
    db.session.commit()
    db.session.close()
  if error:
    abort(500)
    flash('An error occurred. Show could not be listed.')
  else:
    flash('Show was successfully listed!')

  # on successful db insert, flash success

  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
