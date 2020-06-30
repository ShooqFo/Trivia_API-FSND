import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions

def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)
  
  '''
  DONE
  @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs 
  '''
  cors = CORS(app, resources={r"/api/*": {"origins": "*"}}) 
  
  '''
  DONE
  @TODO: Use the after_request decorator to set Access-Control-Allow
  '''

  @app.after_request
  def after_request(response):

    response.headers.add('Access-Control-Allow-Headers','Content-Type,Authorization,true')
    response.headers.add('Access-Control-Allow-Methods','GET,PUT,POST,DELETE,OPTIONS')
    return response


  '''
  @TODO: 
  Create an endpoint to handle GET requests 
  for all available categories.
  '''

  @app.route('/categories')
  def get_categories():
    categories = Category.query.order_by(Category.type).all()
    
    if len(categories) == 0:
     abort(404)

    result = {
      'success': True,
      'categories': {category.id: category.type for category in categories}
      }
    return jsonify(result)


  '''
  
  @TODO: 
  Create an endpoint to handle GET requests for questions, 
  including pagination (every 10 questions). 
  This endpoint should return a list of questions, 
  number of total questions, current category, categories. 

  TEST: At this point, when you start the application
  you should see questions and categories generated,
  ten questions per page and pagination at the bottom of the screen for three pages.
  Clicking on the page numbers should update the questions. 
  '''
  @app.route('/questions')
  def get_questions():
    selection = Question.query.order_by(Question.id).all()
    current_questions = paginate_questions(request, selection)
    categories = Category.query.order_by(Category.type).all()

    if len(current_questions) == 0:
      abort(404)
    
    result = {
            'success': True,
            'questions': current_questions,
            'total_questions': len(selection),
            'current_category': None,
            'categories': {category.id: category.type for category in categories}
    }

    return jsonify(result)

  '''
  DONE
  @TODO: 
  Create an endpoint to DELETE question using a question ID. 

  TEST: When you click the trash icon next to a question, the question will be removed.
  This removal will persist in the database and when you refresh the page. 
  '''
  @app.route("/questions/<int:question_id>", methods=['DELETE'])
  def delete_question(question_id):
    try:
      question = Question.query.filter(Question.id == question_id).one_or_none()

      if question is None:
        abort(404)

      question.delete()
      selection = Question.query.order_by(Question.id).all()
      current_questions = paginate_questions(request, selection)

      return jsonify({
        'success': True,
        'deleted': question_id,
        'questions': current_questions,
        'total_questions': len(Question.query.all())
      })

    except:
      abort(422)

  '''
  @TODO:  DONE
  Create an endpoint to POST a new question, 
  which will require the question and answer text, 
  category, and difficulty score.

  TEST: When you submit a question on the "Add" tab, 
  the form will clear and the question will appear at the end of the last page
  of the questions list in the "List" tab.  
  '''
  @app.route("/questions", methods=['POST'])
  def create_question():
    body = request.get_json()
    
    new_question = body.get('question', None)
    new_answer = body.get('answer', None)
    new_difficulty = body.get('difficulty', None)
    new_category = body.get('category', None)

    try:
      question = Question(question=new_question, answer=new_answer, difficulty=new_difficulty, category=new_category)
      question.insert()

      selection = Question.query.order_by(Question.id).all()
      current_questions = paginate_questions(request, selection)
      result = {
        'success': True,
        'created': question.id,
        'questions': current_questions,
        'total_questions': len(Question.query.all())
      }
      return jsonify(result)

    except:
      abort(422)

  '''
  @TODO: 
  Create a POST endpoint to get questions based on a search term. 
  It should return any questions for whom the search term 
  is a substring of the question. 

  TEST: Search by any phrase. The questions list will update to include 
  only question that include that string within their question. 
  Try using the word "title" to start. 
  '''
  @app.route('/search', methods=['POST'])
  def search_questions():
    search = request.get_json()
    search_term = search.get('search_term', None)
    if search_term:
      search_result = Question.query.filter(Question.question.ilike(f'%{search_term}%')).all()
      question = [question.format() for question in search_results]
      result = {
                'success': True,
                'questions': question,
                'total_questions': len(search_result),
                'current_category': None
            }
      return jsonify(result)
    abort(404)

  '''
  @TODO: DONE
  Create a GET endpoint to get questions based on category. 

  TEST: In the "List" tab / main screen, clicking on one of the 
  categories in the left column will cause only questions of that 
  category to be shown. 
  '''
  
  @app.route('/categories/<int:category_id>/questions', methods=['GET'])
  def get_question(category_id):
    try:
      questions = Question.query.filter(Question.category == str(category_id)).all()
      result = {
        'success': True,
        'questions': [question.format() for question in questions],
        'total_questions': len(questions),
        'current_category': category_id
        }
      return jsonify(result)
    except:
      abort(404)


  '''
  @TODO: 
  Create a POST endpoint to get questions to play the quiz. 
  This endpoint should take category and previous question parameters 
  and return a random questions within the given category, 
  if provided, and that is not one of the previous questions. 

  TEST: In the "Play" tab, after a user selects "All" or a category,
  one question at a time is displayed, the user is allowed to answer
  and shown whether they were correct or not. 
  '''
  @app.route('/play', methods=['POST'])
  def play_quiz():
    try:
      body = request.get_json()
      if not ('category_quiz' in body and 'previous_questions' in body):
         abort(422)
      category = body.get('category_quiz')
      previous_questions = body.get('previous_questions')
      if category['type'] == 'click':
        available_questions = Question.query.filter(Question.id.notin_((previous_questions))).all()
      else:
        available_questions = Question.query.filter_by(category=category['id']).filter(Question.id.notin_((previous_questions))).all()

      new_question = available_questions[random.randrange(0, len(available_questions))].format() if len(available_questions) > 0 else None
      result = {
        'success': True,
        'question': new_question
        }
      return jsonify(result)
    except:
      abort(422)

  '''
  @TODO: DONE
  Create error handlers for all expected errors 
  including 404 and 422. 
  '''
  @app.errorhandler(404)
  def not_found(error):
    return jsonify({
      "success": False,
      "error": 404,
      "message": "Resource not found"
    }), 404
  
  @app.errorhandler(422)
  def unprocessable(error):
    return jsonify({
      "success": False,
      "error": 422,
      "message": "Unprocessable"
    }), 422

  @app.errorhandler(405)
  def method_not_allowed(error):
    return jsonify({
            "success": False,
            "error": 405,
            "message": "The method is not allowed for the requested URL"
        }), 405
      
  return app

    