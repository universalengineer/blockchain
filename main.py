import os, jwt, json, redis
import sentry_sdk

from flask import Flask, send_file, request, jsonify, current_app, Response, g, abort, render_template
from flask.json import JSONEncoder
from flask_cors import CORS
from functools import wraps
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from werkzeug.exceptions import HTTPException
from sentry_sdk.integrations.flask import FlaskIntegration
from celery import Celery, task
from model import UserDao, DeptDao
from service import UserService, DeptService


class Services:
    pass


# 서비스 공통요소 실행
# #Jinja2 Templates 기본폴더 static으로 교체
app = Flask(__name__, template_folder='./static')

CORS(app)

app.config.from_pyfile("config.py")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
database = create_engine(app.config['DB_URL'], encoding='utf-8', pool_size=50, pool_recycle=500, max_overflow=20)
Session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=database))
session = Session()
app.database = database


# Async Logic : 비동기로 요청처리 - Celery + Redis 사용
def make_celery(app):
    celery = Celery(
        app.name,
        broker=app.config['CELERY_BROKER_URL'],
        backend=app.config['CELERY_RESULT_BACKEND']
    )
    celery.conf.update(app.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    return celery


celery = make_celery(app)

r = redis.StrictRedis(host=app.config['REDIS_URL'], port=6379, db=0, password=app.config['REDIS_AUTH'])

# Server Error Tracking - Sentry.io 사용
sentry_sdk.init(
    dsn=app.config['ERROR_SENTRY_URL'],
    integrations=[FlaskIntegration()]
)

# ORM 자동 매핑시에는 아래의 옵션과 같이 활성화 : 본 프로젝트는 DBA와 협업 및 빠르고 직관적인 유지관리 사업을 고려하여 text방식의 SQL문 사용
# models.db.init_app(app)
#
# 서비스 실행순서 참고사항
# before_first_request : 웹 어플리케이션 기동 이후 가장 처음에 들어오는 요청에서만 실행
# before_request : 매 요청시 실행
# after_request :  요청이 끝나 브라우저에 응답하기 전에 실행
# teardown_request : 요청의 결과가 브라우저에 응답하고 난뒤 실행
# teardown_appcontext : HTTP 요청이 완료 되면 실행 되며, 애플리케이션 컨텍스트 내에서 실행
#
#       레이어드(Layered) 아키텍처 패턴 적용
#
#########################################################
#       Persistence Layer
#########################################################
user_dao = UserDao(session)
dept_dao = DeptDao(session)

#########################################################
#       Business Layer
#########################################################
services = Services
services.user_service = UserService(user_dao, app.config)
services.dept_service = DeptService(dept_dao)

#########################################################
#       Presentation Layer
#########################################################
user_service = services.user_service
dept_service = services.dept_service


# HTTP errors (4XX) 핸들러 및 라우팅 처리
# Server errors (500)는 Sentry.io가 처리
@app.errorhandler(HTTPException)
def handle_error(e):
    """ Handle all HTTP exceptions return webpage """
    code = e.code
    return render_template('error.html', code=str(code))


# 서버 보안을 위한 커스텀 헤더 추가
@app.after_request
def add_header(response):
    response.headers['Server'] = 'Server'

    return response


# Default JSON encoder는 set을 JSON으로 변환할 수 없다.
# 그러므로 커스텀 엔코더를 작성하여 set을 list로 변환한다.
class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)

        return JSONEncoder.default(self, obj)


# Flask의 JSON Default 엔코더를 Custom 엔코더로 변경
app.json_encoder = CustomJSONEncoder


# Decorators Pattern
# JWT인증을 통하여 헤더의 access token값이 유효한지 확인
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):

        access_token = request.headers.get('Authorization')
        if access_token is not None:
            try:
                payload = jwt.decode(access_token, current_app.config['JWT_SECRET_KEY'], 'HS256')
            except jwt.InvalidTokenError:
                payload = None
            if payload is None:
                return Response(status=401)
            user_id = payload['user_id']
            g.user_id = user_id
        else:
            return Response(status=401)
        return f(*args, **kwargs)

    return decorated_function


# Decorators Pattern
# 필요에 따라 결과값을 변경하기 위한 커스텀 리턴 구현
def common_response(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            res, res2 = f(*args, **kwargs)

        except Exception as ex:
            res, res2 = str(ex), 500
        return res, res2, {'Server': 'Server'}

    return decorated_function


#########################################################
#       API Endpoints
#########################################################
@app.route("/ping", methods=['GET'])
def ping():

    return 'pong'


@app.route("/error_404", methods=['GET'])
def error_404():
    abort(404)


@app.route("/error_401", methods=['GET'])
def error_401():
    abort(401)


@app.route("/error_403", methods=['GET'])
def error_403():
    abort(403)


@app.route("/error_405", methods=['GET'])
def error_405():
    abort(405)


@app.route("/error_500", methods=['GET'])
def error_500():
    abort(500)


@app.route("/error_sentry", methods=['GET'])
def error_sentry():
    division_by_zero = 1 / 0


@app.route("/sign-up", methods=['POST'])
def sign_up():
    new_user = request.json
    new_user = user_service.create_new_user(new_user)

    return jsonify(new_user)


@app.route('/login', methods=['POST'])
def login():
    credential = request.json
    authorized = user_service.login(credential)

    if authorized:
        user_credential = user_service.get_user_id_and_password(credential['email'])
        user_id = user_credential['id']
        token = user_service.generate_access_token(user_id)

        return jsonify({
            'user_id': user_id,
            'access_token': token
        })
    else:
        return abort(401)


@app.route('/follow', methods=['POST'])
@login_required
def follow():
    payload = request.json
    user_id = g.user_id
    follow_id = payload['follow']
    user_service.follow(user_id, follow_id)

    return '', 200


@app.route('/unfollow', methods=['POST'])
@login_required
def unfollow():
    payload = request.json
    user_id = g.user_id
    unfollow_id = payload['unfollow']
    user_service.unfollow(user_id, unfollow_id)

    return '', 200


@app.route("/hello")
def hello():
    return "Hello World in a uWSGI Nginx Docker container with \
     Python 3.7+ (from the template)"


@app.route("/")
def main():
    index_path = os.path.join(app.static_folder, 'index.html')
    return send_file(index_path)


# Everything not declared before (not a Flask route / API endpoint)...
@app.route('/<path:path>')
def route_frontend(path):
    # ...could be a static file needed by the front end that
    # doesn't use the `static` path (like in `<script src="bundle.js">`)
    file_path = os.path.join(app.static_folder, path)
    if os.path.isfile(file_path):
        return send_file(file_path)
    # ...or should be handled by the SPA's "router" in front end
    else:
        index_path = os.path.join(app.static_folder, 'index.html')
        return send_file(index_path)


#########################################################
#       Redis Test
#########################################################
def GetValues():
    json_val = r.get('val').decode('utf-8')
    result = json.loads(json_val)
    return result


def SetValues(key, val):
    json_val = json.dumps(val, ensure_ascii=False).encode('utf-8')
    r.set(key, json_val)


@app.route("/redis", methods=['POST'])
def redis_test():
    credential = request.json
    SetValues('val', credential['strategy'])
    return jsonify(GetValues())


# r.set('string1', 'pine')
# r.set('string2', 'apple')
#
# p = r.pipeline()
# p.watch('string1', 'string2')  # watch for changes on these keys
# string1 = p.get('string1')
# string2 = p.get('string2')
# p.multi()  # starts transactional block of pipeline
# new_string1 = string1 + string2
# p.set('string1', new_string1)
# p.execute()  # ends transactional block of pipeline


#########################################################
#       Async requests Logic
#########################################################
@task(name='run_scheduled_jobs')
def run_scheduled_jobs():
    print("Celery : 비동기 처리 테스트 AAA")


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
