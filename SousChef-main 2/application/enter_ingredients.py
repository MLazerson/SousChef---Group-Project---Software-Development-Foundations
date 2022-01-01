# blueprint for the enter ingredients views and functionality
import functools
import requests
import json
from flask import (
    Blueprint, flash, g, jsonify, redirect, render_template, request, session, url_for
)
# from werkzeug.security import check_password_hash, generate_password_hash
from application.auth import login_required
from application.db import get_db

bp = Blueprint('enter_ingredients', __name__, url_prefix='/ingredients')

@bp.route('/timer', methods=('GET','POST'))
def set_timer():
    return render_template('index.html')

@bp.route('/share', methods=('GET','POST'))
def share():
    return render_template('share.html')

@bp.route('/enter', methods=('GET','POST'))
@login_required
def send_ingredients():
    # process and send list of ingredients to spoonacular API
    # Make sure to error check input before sending

    db = get_db()

    # if ingredients saved, display ingredients
    list_save_ing = db.execute('SELECT ing_name FROM ingredients WHERE user_id = ?',
        (g.user['id'],)
        ).fetchall()

    error = None

    # TODO: IMPLEMENT SEARCHES WITH SAVED INGREDIENTS AND NEW ING + SAVED ING
    # send ingredient list once user presses submit
    if request.method == 'POST':
        ingredient = request.form['ingredient']
        sortParams = request.form['sort']
        #intolerance checklist
        intolList = ""
        # intolerance checklist
        if request.form.get('intolerance1'):
            intolList += "dairy,"
        if request.form.get('intolerance2'):
            intolList += "peanut,"
        if request.form.get('intolerance3'):
            intolList += "soy,"
        if request.form.get('intolerance4'):
            intolList += "egg,"
        if request.form.get('intolerance5'):
            intolList += "seafood,"
        if request.form.get('intolerance6'):
            intolList += "sulfite,"
        if request.form.get('intolerance7'):
            intolList += "gluten,"
        if request.form.get('intolerance8'):
            intolList += "sesame,"
        if request.form.get('intolerance9'):
            intolList += "tree nut,"
        if request.form.get('intolerance10'):
            intolList += "grain,"
        if request.form.get('intolerance11'):
            intolList += "shellfish,"
        if request.form.get('intolerance12'):
            intolList += "wheat,"

        if ingredient:
            ingredient_parsed = [x.strip() for x in ingredient.split(',')]
        
        if not ingredient and not list_save_ing:
            error = "Ingredient is required."

        if error is None:

            if ingredient:
                for elem in ingredient_parsed:
                    ingredient_ID = hash(elem)
                    # db.execute(
                    #     'INSERT OR IGNORE INTO ingredients (ing_id, ing_name, user_id) VALUES (?,?,?)',
                    #     (ingredient_ID, elem, g.user['id'],)
                    # )

                    if db.execute(
                        'SELECT * FROM ingredients WHERE user_id = ? AND ing_name = ?',
                        (g.user['id'], elem,)
                    ).fetchone() is not None:
                        continue
                    else:
                        db.execute(
                        'INSERT INTO ingredients (ing_id, ing_name, user_id) VALUES (?,?,?)',
                        (ingredient_ID, elem, g.user['id'],)
                    )

                db.commit()

            #concatinate new list of ingredients with saved list
            for saved_ing in list_save_ing:
                ingredient += ', '
                ingredient += saved_ing['ing_name']

                
            return redirect(url_for('enter_ingredients.list_recipes', 
                ingredients=ingredient, 
                intolsList=intolList, sortParams = sortParams))

        flash(error)

    return render_template('enter.html', saved_ing = list_save_ing)


@bp.route('/list', methods=('GET', 'POST'))
@login_required
def list_recipes():

    db = get_db()
    ingredients = request.args.get('ingredients')
    intolerances = request.args.get('intolsList')
    sortKey = request.args.get('sortParams')
    # # GAZE HERE, I AM TRYING TO PRINT THE LIST OF THINGS THAT ARE CHECKED
    # return intolList

    offsetVals = [10, 20, 30, 40, 50, 60]

    if sortKey:
        sortKey = offsetVals[len(sortKey)%5]
        url = 'https://api.spoonacular.com/recipes/complexSearch'
        payload = {'apiKey':'0b74e709a89b45ee987b745c6f53db1a', 
            'includeIngredients' : ingredients,
            'sort' : 'min-missing-ingredients',        
            'intolerances' : intolerances,
            'offset' : sortKey}
    else:
        url = 'https://api.spoonacular.com/recipes/complexSearch'
        payload = {'apiKey':'0b74e709a89b45ee987b745c6f53db1a', 
            'includeIngredients' : ingredients,
            'sort' : 'min-missing-ingredients',        
            'intolerances' : intolerances}
    
    r = requests.get(url, params=payload)

    results = r.json()

    #return results#["results"]

    # resstr = ""

    # for item in results["results"]:
    #     resstr += item["title"] + " | "

    # return resstr

    for recipe in results["results"]:
        db.execute(
            'INSERT OR IGNORE INTO recipes (user_id, id, rec_name, rec_img) VALUES (?,?,?,?)', 
            (g.user['id'], recipe['id'], recipe['title'], recipe['image'],)
        )
    
    db.commit()

    return render_template('receiveRecipespurehtml.html', recipes=results["results"])

@bp.route('/recipes/', methods=('GET', 'POST'))
@login_required
def recipes():
    
    recipe_ID = request.args.get('selected_id')

    url = 'https://api.spoonacular.com/recipes/{}/information'.format(recipe_ID)
    payload = {'apiKey':'0b74e709a89b45ee987b745c6f53db1a'}

    
    r = requests.get(url, params=payload)

    recipe = r.json()

    # extract recipe API endpoint

    url = 'https://api.spoonacular.com/recipes/extract'
    payload = {
        'apiKey':'0b74e709a89b45ee987b745c6f53db1a',
        'url': recipe['sourceUrl']
    }

    r = requests.get(url, params=payload)

    recipeInfo = r.json()

    return redirect(url_for('enter_ingredients.instructions', title=recipeInfo['title'], time=recipeInfo['readyInMinutes']
    , servings=recipeInfo['servings'], image=recipeInfo['image'], instructions=recipeInfo['instructions'],
    link=recipeInfo['sourceUrl'], rec_ID = recipe_ID))


    #return str(recipe['title']) + str(recipe['sourceUrl'])
    #return redirect(recipe['sourceUrl'])

@bp.route('/history', methods=['GET'])
@login_required
def recipe_history():

    db = get_db()

    # receive history of all viewed recipes showing most recent first
    rec_hist = db.execute(
        'SELECT id, rec_name, rec_img FROM recipes WHERE user_id = ? ORDER BY created DESC',
        (g.user['id'],)
    ).fetchall()

    return render_template('list_rec_history.html', recipes=rec_hist)

@bp.route('/instructions', methods=['GET','POST'])
@login_required
def instructions():

    recipeTitle = request.args.get('title')
    recipeTime = request.args.get('time')
    recipeServings = request.args.get('servings')
    recipeImage = request.args.get('image')
    recipeInstructions = request.args.get('instructions')
    recipeLink = request.args.get('link')
    recipeID = request.args.get('rec_ID')
    #recipeInfo = json.loads(recipeInfo)
    db = get_db()

    recipeRating = db.execute('SELECT rating FROM recipes WHERE user_id = ? AND id = ?',
        (g.user['id'],recipeID,)).fetchone()

    recipeNotes = db.execute('SELECT notepad FROM recipes WHERE user_id = ? AND id = ?',
        (g.user['id'],recipeID)).fetchone()
    
    db.commit()

    if recipeRating:
        recipeRating = recipeRating[0]
    
    if recipeNotes:
        recipeNotes = recipeNotes[0]

    if request.method == 'POST':
        
        if request.form.get('rate'):
            recipeRating = request.form.get('rate')
            recipeNotes = request.form.get('notepad')

            db.execute('UPDATE recipes SET rating = ? WHERE user_id = ? AND id = ?',
                (recipeRating, g.user['id'], recipeID,))
            
            db.execute('UPDATE recipes SET notepad = ? WHERE user_id = ? AND id = ?',
                (recipeNotes, g.user['id'], recipeID,))

            db.commit()

        return render_template('recipeInstructions.html', title=recipeTitle, time=recipeTime,
        servings=recipeServings, image=recipeImage, instructions=recipeInstructions,
        link=recipeLink, rating = recipeRating, notes=recipeNotes)

    # return str(g.user['id'])
    return render_template('recipeInstructions.html', title=recipeTitle, time=recipeTime
    , servings=recipeServings, image=recipeImage, instructions=recipeInstructions,
    link=recipeLink, rating=recipeRating, notes=recipeNotes)

@bp.route('/random', methods=('GET', 'POST'))
@login_required
def ran_recipe():
    recips = [540657,462729,666439,263549,262918]
    size= 4
    from numpy import random
    rand_num =  random.randint(4)
    ingredients = request.args.get('ingredients')
    url = 'https://api.spoonacular.com/recipes/{}/information'.format(recips[rand_num])
    payload = {'apiKey':'0b74e709a89b45ee987b745c6f53db1a'}
    
    r = requests.get(url, params=payload)


    results = r.json()

    return redirect(results['sourceUrl'])