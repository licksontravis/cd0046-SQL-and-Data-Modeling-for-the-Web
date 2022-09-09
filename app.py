#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import sys
import dateutil.parser
import babel
from flask import render_template, request, flash, redirect, url_for, abort
import logging
from logging import Formatter, FileHandler
from forms import *
from models import *

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

def format_datetime_to_string(v):
  return "{}-{}-{} {}".format(
        v.strftime("%Y"),
        v.strftime("%m"),
        v.strftime("%d"),
        v.strftime("%H:%M:%S")
      )
#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------
"""
Handle GET requests for all available venues.
"""
@app.route('/venues')
def venues():

  data = []
  current_time = datetime.now()
  for v in db.session.query(Venue.city, Venue.state).distinct():
    venueItem = []
    for ven in db.session.query(Venue.id, Venue.name).filter(Venue.city==v.city).all():
      venueItem.append({
        "id": ven.id,
        "name": ven.name,
        "num_upcoming_shows": Show.query.filter(Show.venue_id==ven.id).filter(Show.start_time>current_time).count()
      })
    data.append({
      "city": v.city,
      "state": v.state,
      "venues": venueItem
    })
  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  
  search_term = request.form.get('search_term', '')
  rsearch = db.session.query(Venue).filter(Venue.name.ilike('%{}%'.format(search_term))).all()
  data = []
  for r in rsearch:
    data.append({
      "id": r.id,
      "name": r.name,
    })
  response={
    "count": len(rsearch),
    "data": data
  }
  return render_template('pages/search_venues.html', results=response, search_term=search_term )

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):

  venue = Venue.query.get(venue_id)
  pastShowsDataSet = db.session.query(Show).join(Venue).filter(Show.artist_id==venue_id).filter(Show.start_time<datetime.now()).all()  
  past_shows = []
  for s in pastShowsDataSet:
    a = Artist.query.get(s.artist_id)
    past_shows.append({
        "artist_id": a.id,
        "artist_name": a.name,
        "artist_image_link": a.image_link,
        "start_time": format_datetime_to_string(s.start_time)        
    })
    
  upcomingShowsDataset = db.session.query(Show).join(Venue).filter(Show.artist_id==venue_id).filter(Show.start_time>datetime.now()).all()
  upcoming_shows = []
  for s in upcomingShowsDataset:
    a = Artist.query.get(s.artist_id)
    upcoming_shows.append({
        "artist_id": a.id,
        "artist_name": a.name,
        "artist_image_link": a.image_link,
        "start_time": format_datetime_to_string(s.start_time)        
    })

  data={
    "id": venue_id,
    "name": venue.name,
    "genres": [venue.genres],
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website_link,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows),
  }
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET','POST'])
def create_venue_submission():
  error = False
  form = VenueForm()
  if form.validate_on_submit():
    try:
      venue = Venue(
        name=form.name.data, 
        city=form.city.data, 
        state=form.state.data, 
        address=form.address.data,
        phone=form.phone.data, 
        image_link=form.image_link.data, 
        genres=form.genres.data,
        facebook_link=form.facebook_link.data, 
        website_link=form.website_link.data, 
        seeking_talent=form.seeking_talent.data, 
        seeking_description=form.seeking_description.data
      )
      
      db.session.add(venue)
      db.session.commit()   
    except:
      db.session.rollback()
      error = True
      print(sys.exc_info())
    finally:
      db.session.close()
    if error:
      # TODO: on unsuccessful db insert, flash an error instead.
      flash('An error occurred. Venue ' + form.name.data + ' could not be listed.')
      abort(500)
    else:
      # on successful db insert, flash success
      flash('Venue ' + form.name.data + ' was successfully listed!')
      return render_template('pages/home.html')
    # e.g., 
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  else:
    return render_template('forms/new_venue.html', form=form)
  

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):

  error=False
  data = []
  try:
    venue = Venue.query.get(venue_id)
    data['name'] = venue.name
    db.session.delete(venue)
    db.session.commit()
  except:
    db.session.rollback()
    error = True
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    # TODO: on unsuccessful db delete, flash an error instead.
    flash('An error occurred. Venue ' + data['name'] + ' could not be removed.')
    abort(500)
  else:
    # on successful db insert, flash success
    flash('Venue ' + data['name'] + ' was successfully deleted!')  
    return redirect(url_for('/venues'))

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  #return None

#  Artists
#  ----------------------------------------------------------------
"""
Handle GET requests for all available artists.
"""
@app.route('/artists')
def artists():

  data = db.session.query(Artist.id, Artist.name).all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():

  search_term = request.form.get('search_term', '')
  rsearch = db.session.query(Artist).filter(Artist.name.ilike('%{}%'.format(search_term))).all()
  data = []
  for r in rsearch:
    data.append({
      "id": r.id,
      "name": r.name,
    })
  response={
    "count": len(rsearch),
    "data": data
  }
  return render_template('pages/search_artists.html', results=response, search_term=search_term)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  
  artist = Artist.query.get(artist_id)
  pastShowsDataset = db.session.query(Show).join(Venue).filter(Show.artist_id==artist_id).filter(Show.start_time<datetime.now()).all()
  past_shows = []
  for s in pastShowsDataset:
    v = Venue.query.get(s.venue_id)
    past_shows.append({
        "venue_id": v.id,
        "venue_name": v.name,
        "venue_image_link": v.image_link,
        "start_time": format_datetime_to_string(s.start_time)        
    })

  upcomingShowsDataset = db.session.query(Show).join(Venue).filter(Show.artist_id==artist_id).filter(Show.start_time>datetime.now()).all()
  upcoming_shows = []
  for s in upcomingShowsDataset:
    v = Venue.query.get(s.venue_id)
    upcoming_shows.append({
        "venue_id": v.id,
        "venue_name": v.name,
        "venue_image_link": v.image_link,
        "start_time": format_datetime_to_string(s.start_time)        
    })

  data={
    "id": artist_id,
    "name": artist.name,
    "genres": [artist.genres.replace("{","").replace("}","")],
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website_link,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows),
  }
  return render_template('pages/show_artist.html', artist=data)

#  Update Artist
#  ----------------------------------------------------------------

@app.route('/artists/<int:artist_id>/edit', methods=['GET','POST'])
def edit_artist(artist_id):
  # artist record with ID <artist_id> using the new attributes

  form = ArtistForm()
  artist = Artist.query.get(artist_id)
  error = False
  if form.validate_on_submit():
    try:
      artist = Artist.query.get(artist_id)

      artist.name=form.name.data
      artist.city=form.city.data
      artist.state=form.state.data
      artist.phone=form.phone.data
      artist.genres=form.genres.data
      artist.facebook_link=form.facebook_link.data
      artist.image_link=form.image_link.data
      artist.website_link=form.website_link.data
      artist.seeking_venue=form.seeking_venue.data
      artist.seeking_description=form.seeking_description.data

      db.session.add(artist)
      db.session.commit()
    except:
      db.session.rollback()
      error = True
      print(sys.exc_info())
    finally:
      db.session.close()
    if error:
      # on unsuccessful db insert, flash an error instead.
      flash('An error occurred. Artist ' + form.name.data + ' could not be listed.')
      abort(500)
    else:
      # on successful db insert, flash success
      flash('Artist ' + form.name.data + ' was successfully listed!')  
      return redirect(url_for('show_artist', artist_id=artist_id))
  else:
    form.name.data = artist.name
    form.city.data = artist.city
    form.state.data = artist.state
    form.phone.data = artist.phone
    form.image_link.data = artist.image_link
    form.genres.data = artist.genres
    form.facebook_link.data = artist.facebook_link
    form.website_link.data = artist.website_link
    form.seeking_description.data = artist.seeking_description
    
    return render_template('forms/edit_artist.html', form=form, artist=artist)

#  Update Venue
#  ----------------------------------------------------------------

@app.route('/venues/<int:venue_id>/edit', methods=['GET','POST'])
def edit_venue_submission(venue_id):
  # take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes

  form = VenueForm()
  venue = Venue.query.get(venue_id)
  error = False
  if form.validate_on_submit():
    try:
      venue.name=form.name.data
      venue.city=form.city.data
      venue.state=form.state.data
      venue.address=form.address.data
      venue.phone=form.phone.data
      venue.image_link=form.image_link.data
      venue.genres=form.genres.data
      venue.facebook_link=form.facebook_link.data
      venue.website_link=form.website_link.data
      venue.seeking_talent=form.seeking_talent.data
      venue.seeking_description=form.seeking_description.data

      db.session.add(venue)
      db.session.commit()
    except:
      db.session.rollback()
      error = True
      print(sys.exc_info())
    finally:
      db.session.close()
    if error:
      # on unsuccessful db insert, flash an error instead.
      flash('An error occurred. Venue ' + form.name.data + ' could not be listed.')
      abort(500)
    else:
      # on successful db insert, flash success
      flash('Venue ' + form.name.data + ' was successfully listed!')  
      return redirect(url_for('show_venue', venue_id=venue_id))
  else:
    # populate form with values from venue with ID <venue_id>
    form.name.data = venue.name
    form.city.data = venue.city
    form.state.data = venue.state
    form.address.data = venue.address
    form.phone.data = venue.phone
    form.image_link.data = venue.image_link
    form.genres.data = venue.genres
    form.facebook_link.data = venue.facebook_link
    form.website_link.data = venue.website_link
    form.seeking_talent.data = venue.seeking_talent
    form.seeking_description.data = venue.seeking_description

    return render_template('forms/edit_venue.html', form=form, venue=venue)

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET','POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  error = False
  form = ArtistForm()
  if form.validate_on_submit():
    try:
      if form.validate_on_submit():
        artist = Artist(
          name=form.name.data, 
          city=form.city.data, 
          state=form.state.data,
          phone=form.phone.data,
          image_link=form.image_link.data,
          genres=form.genres.data,
          facebook_link=form.facebook_link.data,
          website_link=form.website_link.data,
          seeking_venue=form.seeking_venue.data,     
          seeking_description=form.seeking_description.data
        )
        
        db.session.add(artist)
        db.session.commit()    
    except:
      db.session.rollback()
      error = True
      print(sys.exc_info())
    finally:
      db.session.close()
    if error:
      # on unsuccessful db insert, flash an error instead.
      flash('An error occurred. Artist ' + form.name.data + ' could not be listed.')
      abort(500)
    else:
      # on successful db insert, flash success
      flash('Artist ' + form.name.data + ' was successfully listed!')
      return render_template('pages/home.html')
  else:
    return render_template('forms/new_artist.html', form=form)

#  Shows
#  ----------------------------------------------------------------
"""
Handle GET requests for all available shows
"""
@app.route('/shows')
def shows():
  # displays list of shows at /shows

  data = []
  for s in Show.query.all():
    a = Artist.query.get(s.artist_id)
    v = Venue.query.get(s.venue_id)
    data.append({
      "venue_id": s.venue_id,
      "venue_name": v.name,
      "artist_id": s.artist_id,
      "artist_name": a.name,
      "artist_image_link": a.image_link,
      "start_time": "{}-{}-{} {}".format(
        s.start_time.strftime("%Y"),
        s.start_time.strftime("%m"),
        s.start_time.strftime("%d"),
        s.start_time.strftime("%H:%M:%S")
      )
    })
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

"""
POST a new show. Require the id artist and id venue.
"""
@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form

  form = ShowForm()
  if form.validate_on_submit():
    error = False
    try:
      show = Show(
        artist_id=int(form.artist_id.data),
        venue_id=int(form.venue_id.data),
        start_time=form.start_time.data
      )
      
      artist = Artist.query.filter(Artist.id==int(form.artist_id.data)).first()
      venue = Venue.query.filter(Venue.id==int(form.venue_id.data)).first()

      artist.shows.append(show)
      venue.shows.append(show)
      
      db.session.add(show)
      db.session.add(artist)
      db.session.add(venue)
      db.session.commit()
    except:
      db.session.rollback()
      error = True
      print(sys.exc_info())    
    finally:
      db.session.close()
    if error:
      # on unsuccessful db insert, flash an error instead.
      flash('An error occurred. Show could not be listed.')
      abort(500)
    else:
      # on successful db insert, flash success
      flash('Show was successfully listed!')
      return render_template('pages/home.html')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/

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

#if __name__ == '__main__':
#    app.run()


# Or specify port manually:
if __name__ == '__main__':
    #port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=3000)
