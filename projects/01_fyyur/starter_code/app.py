#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#
import dateutil.parser
import babel
from flask import (
    Flask,
    render_template,
    request,
    flash,
    redirect,
    url_for
)
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler


from forms import *
from models import *

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

migrate = Migrate(app, db)

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
    '''
    venues = Venue.query.order_by(desc(Venue.created_date)).limit(10).all()
    artists = Artist.query.order_by(desc(Artist.created_date)).limit(10).all()
    return render_template('pages/home.html', venues=venues, artists=artists)
    NOTE: Adding this code would require changes to my artist and venue models.
    '''

#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():

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

    term = request.form.get('search_term')

    venues = Venue.query.filter(Venue.name.ilike('%'+term+'%')).all()

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

  # error = False
  #
  # try:
  #   name = request.form.get('name')
  #   city = request.form.get('city')
  #   state = request.form.get('state')
  #   address = request.form.get('address')
  #   phone = request.form.get('phone')
  #   genres = request.form.getlist('genres')
  #   facebook_link = request.form.get('facebook_link')
  #   venue = Venue(name=name, city=city, state=state, address=address, phone=phone, genres=genres, facebook_link=facebook_link)
  #   db.session.add(venue)
  # except():
  #   db.session.rollback()
  #   error = True
  #   print(sys.exc_info())
  # finally:
  #   db.session.commit()
  #   db.session.close()
  # if error:
  #   abort(500)
  #   flash('An error occurred. Venue ' + name + ' could not be listed.')
    # if error flash error message
  # else:
  #   flash('Venue ' + request.form['name'] + ' was successfully listed!')
    # on successful db insert, flash success
  form = VenueForm(request.form)
  try:
      venue = Venue()
      form.populate_obj(venue)
      db.session.add(venue)
      db.session.commit()
      flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except ValueError as e:
      print(e)
      flash('An error occurred. ' + request.form['name'] + ' could not be listed.')
      db.session.rollback()
  finally:
      db.session.close()

  return render_template('pages/home.html')
# Create Vendor code changed to use VenueForm and code suggested by Reviewer /reviews/2791179

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

    term = request.form.get('search_term')

    artists = Artist.query.filter(Artist.name.ilike('%'+term+'%')).all()

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
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):

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

  # error = False
  #
  # try:
  #   name = request.form.get('name')
  #   city = request.form.get('city')
  #   state = request.form.get('state')
  #   phone = request.form.get('phone')
  #   genres = request.form.getlist('genres')
  #   facebook_link = request.form.get('facebook_link')
  #   artist = Artist(name=name, city=city, state=state, phone=phone, genres=genres, facebook_link=facebook_link)
  #   db.session.add(artist)
  # except():
  #   db.session.rollback()
  #   error = True
  #   print(sys.exc_info())
  # finally:
  #   db.session.commit()
  #   db.session.close()
  # if error:
  #   abort(500)
  #   flash('An error occurred. Artist ' + name + ' could not be listed.')
  #   # if error flash error message
  # else:
  #   flash('Artist ' + request.form['name'] + ' was successfully listed!')
  #   # on successful db insert, flash success
  form = ArtistForm(request.form)
  try:
      artist = Artist()
      form.populate_obj(artist)
      db.session.add(artist)
      db.session.commit()
      flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except ValueError as e:
      print(e)
      flash('An error occurred. ' + request.form['name'] + ' could not be listed.')
      db.session.rollback()
  finally:
      db.session.close()
  return render_template('pages/home.html')
# Create Artist code changed to use ArtistForm and code suggested by Reviewer /reviews/2791179


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

  # error = False
  #
  # try:
  #   artist_id = request.form.get('artist_id')
  #   venue_id = request.form.get('venue_id')
  #   start_time = request.form.get('start_time')
  #   show = Shows(artist_id=artist_id, venue_id=venue_id, start_time=start_time)
  #   db.session.add(show)
  # except():
  #   db.session.rollback()
  #   error = True
  #   print(sys.exc_info())
  # finally:
  #   db.session.commit()
  #   db.session.close()
  # if error:
  #   abort(500)
  #   flash('An error occurred. Show could not be listed.')
  #   # if error flash error message
  # else:
  #   flash('Show was successfully listed!')
   # on successful db insert, flash success
  form = ShowForm(request.form)
  try:
      show = Shows()
      form.populate_obj(show)
      db.session.add(show)
      db.session.commit()
      flash('Show ' + request.form['artist_id'] + ' was successfully listed!')
  except ValueError as e:
      print(e)
      flash('An error occurred. ' + request.form['artist_id'] + ' could not be listed.')
      db.session.rollback()
  finally:
      db.session.close()
  return render_template('pages/home.html')

# Create Show code changed to use ShowForm and code suggested by Reviewer /reviews/2791179


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
