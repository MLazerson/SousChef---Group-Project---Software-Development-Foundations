import functools
import requests
import json
import numpy
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)

@bp.route('/randoms', methods=('GET', 'POST'))
@login_required
def ran_recipe():
	cuisines = ['African','American','British','Caribbean','Chinese','French','German','Greek','Indian','Irish','Italian','Japanese','Jewish','Korean']
	size= 13

	#rand_num =  numpy.random.randint(13)
    ingredients = request.args.get('ingredients')
    url = 'https://api.spoonacular.com/recipes/complexSearch?cuisine={}'.format(cuisines[0])
    payload = {'apiKey':'0b74e709a89b45ee987b745c6f53db1a'}
    
    r = requests.get(url, params=payload)


    results = r.json()

    return render_template('random_recipe.html', recipes=results)
