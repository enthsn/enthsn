import sqlite3
from kodi_six import xbmc

##
# Looks at the cache and return the movie details.
##
def get_cached_movie_details(cache_db_file, id):
	try :
		conn = sqlite3.connect(cache_db_file)
		cursor = conn.cursor()

		# Check whether we have a table, otherwise create the table
		# Maybe there is a better way of doing this.
		cursor.execute('CREATE TABLE IF NOT EXISTS movie_detail_cache(id text, name text, image text)')
		cursor.execute('SELECT id, name, image FROM movie_detail_cache WHERE id=' + str(id))
		cached_results = cursor.fetchall()

		if (len (cached_results) > 0):
			return cached_results[0]
	except :
		xbmc.log("Exception while getting cached movie detail", xbmc.LOGERROR)
		return None


##
# Saves a new movie to the cache. Does *not* check for duplication.
##
def save_move_details_to_cache(cache_db_file, id, name, picture):
	try :
		conn = sqlite3.connect(cache_db_file)
		cursor = conn.cursor()
		cursor.execute('INSERT INTO movie_detail_cache VALUES ("'+str(id)+'","'+str(name)+'","'+str(picture)+ '")')
		conn.commit()
	except:
		xbmc.log("Exception while saving movie detail to cache", xbmc.LOGERROR)
		return None
		
