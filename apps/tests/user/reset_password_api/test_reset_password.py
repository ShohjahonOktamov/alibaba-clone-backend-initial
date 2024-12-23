import pytest
from django.contrib.auth.hashers import check_password
from user.models import User, Group

from rest_framework.exceptions import ValidationError


@pytest.fixture()
def forgot_password_data(request, user_factory, mocker):
    user = user_factory.create()
    return_data = {
        'status_code': 200,
        'redis_conn': None,
        'phone_exists': None,
        'generate_otp': None,
        'send_email': None,
        'req_json': {
            'email': user.email,
        },
    }

    def valid_data():
        redis_conn = mocker.Mock()
        redis_conn.exists.return_value = False
        return_data.update({
            'redis_conn': redis_conn,
            'generate_otp': ('123456', '1v8z0OmsbndfkJ0XI3cpNcHWrofrHZfY0oGJZbvGW4siTs0'),
            'send_email': 200
        })
        return return_data

    def not_send_otp_code():
        redis_conn = mocker.Mock()
        redis_conn.exists.return_value = False
        return_data.update({
            'status_code': 400,
            'redis_conn': redis_conn,
            'generate_otp': ('123456', '1v8z0OmsbndfkJ0XI3cpNcHWrofrHZfY0oGJZbvGW4siTs0'),
            'send_email': 400
        })
        return return_data

    def exists_otp_code():
        redis_conn = mocker.Mock()
        redis_conn.exists.return_value = True
        redis_conn.get.return_value = b'asfasdI&UJHGasJHKLHJkjhasklfh9839klajhk'
        return_data.update({
            'redis_conn': redis_conn
        })
        return return_data

    def invalid_email():
        return_data.update({'status_code': 400})
        return_data['req_json'].update({'email': 'invalid_email'})
        return return_data

    def required_email():
        return_data.update({'status_code': 400})
        return_data['req_json'].pop('email')
        return return_data

    def empty_email():
        return_data.update({'status_code': 400})
        return_data['req_json'].update({'email': ''})
        return return_data

    def not_exists_email():
        return_data.update({'status_code': 400})
        return_data['req_json'].update({'email': 'testemail@gmail.com'})
        return return_data

    data = {
        'valid_data': valid_data,
        'not_send_otp_code': not_send_otp_code,
        'exists_otp_code': exists_otp_code,
        'required_email': required_email,
        'invalid_email': invalid_email,
        'empty_email': empty_email,
        'not_exists_email': not_exists_email,
    }
    return data[request.param]


@pytest.mark.django_db
@pytest.mark.parametrize(
    'forgot_password_data',
    [
        'valid_data',
        'not_send_otp_code',
        'exists_otp_code',
        'required_email',
        'invalid_email',
        'empty_email',
        'not_exists_email',
    ],
    indirect=True,
)
def test_forgot_password(request, forgot_password_data, api_client, mocker):
    test_name = request.node.name
    return_data = forgot_password_data()

    redis_conn = return_data['redis_conn']
    mocker.patch('user.views.redis_conn', redis_conn)
    mocker.patch('user.views.generate_otp', return_value=return_data['generate_otp'])
    mocker.patch('user.views.send_email', return_value=return_data['send_email'])

    client = api_client()
    resp = client.post('/api/users/password/forgot/', data=return_data['req_json'], format='json')
    assert resp.status_code == return_data['status_code']

    if resp.status_code == 200:
        resp_json = resp.json()
        assert sorted(resp_json.keys()) == sorted(['email', 'otp_secret'])

    if test_name == 'test_forgot_password[not_send_otp_code]':
        redis_conn.delete.assert_called_once_with(f"{return_data['req_json']['email']}:otp")


@pytest.fixture
def forgot_password_verify_data(request, mocker, user_factory):
    user = user_factory.create()
    return_data = {
        'status_code': 200,
        'redis_conn': None,
        'check_otp': None,
        'exists_otp': None,
        'req_json': {
            'otp_code': '123456',
            'email': user.email,
        },
        'otp_secret': None,
    }

    def valid_data():
        redis_conn = mocker.Mock()
        redis_conn.delete.return_value = 1
        redis_conn.set.return_value = True
        return_data.update({
            'redis_conn': redis_conn,
            'otp_secret': 'asfasdI&UJHGasJHKLHJkjhasklfh9839klajhk'
        })
        return return_data

    def invalid_otp():
        redis_conn = mocker.Mock()
        return_data.update({
            'status_code': 400,
            'redis_conn': redis_conn,
            'exists_otp': ValidationError("Invalid OTP code.", 400),
            'otp_secret': 'asfasdI&UJHGasJHKLHJkjhasklfh9839klajhk'
        })
        return return_data

    def required_otp_code():
        return_data.update({'status_code': 400})
        return_data['req_json'].pop('otp_code')
        return return_data

    def required_email():
        return_data.update({'status_code': 400})
        return_data['req_json'].pop('email')
        return return_data

    def invalid_email():
        return_data.update({'status_code': 400})
        return_data['req_json'].update({'email': 'invalid_email'})
        return return_data

    def empty_otp_secret():
        return_data.update({
            'status_code': 404,
            'otp_secret': ''
        })
        return return_data

    data = {
        'valid_data': valid_data,
        'invalid_otp': invalid_otp,
        'required_otp_code': required_otp_code,
        'required_email': required_email,
        'invalid_email': invalid_email,
        'empty_otp_secret': empty_otp_secret
    }
    return data[request.param]


@pytest.mark.django_db
@pytest.mark.parametrize(
    'forgot_password_verify_data',
    [
        'valid_data',
        'invalid_otp',
        'required_otp_code',
        'required_email',
        'invalid_email',
        'empty_otp_secret'
    ],
    indirect=True
)
def test_forgot_password_verify(forgot_password_verify_data, api_client, mocker):
    return_data = forgot_password_verify_data()

    redis_conn = return_data['redis_conn']
    mocker.patch('user.views.redis_conn', redis_conn)
    mocker.patch('user.views.check_otp', return_value=return_data['check_otp'],
                 side_effect=return_data['exists_otp'])
    mocker.patch('user.views.make_password', return_value='mocked_token_hash')

    client = api_client()
    otp_secret = return_data['otp_secret']

    resp = client.post(
        f'/api/users/password/forgot/verify/{otp_secret}/',
        data=return_data['req_json'], format='json'
    )
    assert resp.status_code == return_data['status_code']

    if resp.status_code == 200:
        resp_json = resp.json()
        assert sorted(resp_json.keys()) == sorted(['token'])

        redis_conn.delete.assert_any_call(f"{return_data['req_json']['email']}:otp")

        redis_conn.set.assert_any_call('mocked_token_hash', return_data['req_json']['email'], ex=2 * 60 * 60)


@pytest.fixture()
def reset_password_data(request, mocker, user_factory):
    user = user_factory.create()
    buyer_group = Group.objects.get(name="buyer")
    user.groups.add(buyer_group)
    user.save()
    password = 'KJmkds87jhHTF32jhb'
    return_data = {
        'status_code': 200,
        'redis_conn': None,
        'reset_password': None,
        'email': user.email,
        'req_json': {
            'token': user.email.encode(),
            'password': password,
            'confirm_password': password,
        },
    }

    def valid_data():
        redis_conn = mocker.Mock()
        redis_conn.get.return_value = user.email.encode()
        return_data.update({
            'redis_conn': redis_conn,
            'reset_password': user,
        })
        return return_data

    def required_token():
        return_data.update({'status_code': 400})
        return_data['req_json'].pop('token')
        return return_data

    def invalid_token():
        redis_conn = mocker.Mock()
        redis_conn.get.return_value = None
        return_data.update({
            'status_code': 400,
            'redis_conn': redis_conn,
        })
        return return_data

    def invalid_password():
        return_data.update({
            'status_code': 400,
            'req_json': {
                'token': 'valid_token',
                'password': 'short',
                'confirm_password': 'short',
            },
        })
        return return_data

    def required_password():
        return_data.update({'status_code': 400})
        return_data['req_json'].pop('password')
        return return_data

    def empty_password():
        return_data.update({'status_code': 400})
        return_data['req_json'].update({'password': ''})
        return return_data

    def password_mismatch():
        return_data.update({'status_code': 400})
        return_data['req_json'].update({'confirm_password': 'mismatch'})
        return return_data

    def required_confirm_password():
        return_data.update({'status_code': 400})
        return_data['req_json'].pop('confirm_password')
        return return_data

    def empty_confirm_password():
        return_data.update({'status_code': 400})
        return_data['req_json'].update({'confirm_password': ''})
        return return_data

    def empty_request():
        return_data.update({'status_code': 400})
        return_data['req_json'] = dict()
        return return_data

    data = {
        'valid_data': valid_data,
        'required_token': required_token,
        'invalid_token': invalid_token,
        'invalid_password': invalid_password,
        'password_mismatch': password_mismatch,
        'required_password': required_password,
        'empty_password': empty_password,
        'required_confirm_password': required_confirm_password,
        'empty_confirm_password': empty_confirm_password,
        'empty_request': empty_request
    }
    return data[request.param]


@pytest.mark.django_db
@pytest.mark.parametrize(
    'reset_password_data',
    [
        'valid_data',
        'required_token',
        'invalid_token',
        'invalid_password',
        'password_mismatch',
        'required_password',
        'empty_password',
        'required_confirm_password',
        'empty_confirm_password',
        'empty_request'
    ],
    indirect=True
)
def test_reset_password(reset_password_data, api_client, mocker):
    return_data = reset_password_data()
    redis_conn = return_data['redis_conn']
    mocker.patch('user.views.redis_conn', redis_conn)

    client = api_client()
    resp = client.patch(
        '/api/users/password/reset/',
        data=return_data['req_json'], format='json'
    )
    assert resp.status_code == return_data['status_code']

    if resp.status_code == 200:
        resp = resp.json()
        assert sorted(resp.keys()) == sorted(['access', 'refresh'])

        token_hash = return_data['email']
        redis_conn.delete.assert_called_once_with(token_hash)

        email = return_data['email']
        user = User.objects.get(email=email)
        assert check_password(return_data['req_json']['password'], user.password)
