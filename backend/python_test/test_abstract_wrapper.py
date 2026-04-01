import pytest
from data.data_wrappers import wrappers
from uuid import uuid4
@pytest.fixture
def wrapper():
    wrapper=wrappers.AROUsersWrapper()
    return wrapper
@pytest.fixture
def obj1():
    obj={
        "call_sign":"12333",
        "email":"testing123@gmail.com",
        "first_name":"John",
        "last_name":"Doe",
        "phone_number":"123-456-7890"
    }
    return obj
@pytest.fixture
def obj2():
    obj2={
        "call_sign":"45673",
        "email":"object2@gmail.com",
        "first_name":"Jane",
        "phone_number":"423-274-4232"
    }
    return obj2

def test_create(wrapper,obj1,obj2):
    result=wrapper.create(obj1)
    assert result.call_sign==obj1["call_sign"]
    assert result.email==obj1["email"]
    assert result.first_name==obj1["first_name"]
    assert result.last_name==obj1["last_name"]
    assert result.phone_number==obj1["phone_number"]
    result=wrapper.create(obj2)
    assert result.call_sign==obj2["call_sign"]
    assert result.email==obj2["email"]
    assert result.first_name==obj2["first_name"]
    assert result.phone_number==obj2["phone_number"]

def test_get_all(wrapper,obj1,obj2):
    wrapper.create(obj1)
    wrapper.create(obj2)
    arr=wrapper.get_all()
    assert arr[0].email==obj1["email"] or arr[0].email==obj2["email"]
    if arr[0].email==obj1["email"]:
        assert arr[1].email==obj2["email"]
    else:
        assert arr[1].email==obj1["email"]

def test_get_by_id(wrapper,obj1):
    get=wrapper.create(obj1)
    obj=wrapper.get_by_id(get.id)
    assert obj.id==get.id
    random_id=uuid4()
    err=None
    try:
        obj=wrapper.get_by_id(random_id)
    except ValueError as e:
        err=type(e)
    finally:
        assert err==ValueError


def test_delete_by_id(wrapper,obj1):
    delete=wrapper.create(obj1)
    obj=wrapper.delete_by_id(delete.id)
    assert obj.id==delete.id
    assert not wrapper.get_all()
    random_id=uuid4()
    err=None
    try:
        obj=wrapper.delete_by_id(random_id)
    except ValueError as e:
        err=type(e)
    finally:
        assert err==ValueError

def test_update(wrapper,obj1):
    obj=wrapper.create(obj1)
    assert obj.email==obj1["email"]
    new_info=obj1.copy()
    new_info["email"]="new_email@gmail.com"
    new_obj=wrapper.update(obj.id,new_info)
    assert new_obj.email==new_info["email"]
    new_info=obj1.copy()
    new_info["random_field"]="random"
    err=None
    try:
        new_obj=wrapper.update(obj.id,new_info)
    except Exception as e:
        err=type(e)
    finally:
        assert err==ValueError
    new_info=obj1.copy()
    new_info["id"]=uuid4()
    err=None
    try:
        new_obj=wrapper.update(obj.id,new_info)
    except Exception as e:
        err=type(e)
    finally:
        assert err==ValueError
    err=None
    new_info=obj1.copy()
    new_info["email"]=4
    try:
        new_obj=wrapper.update(obj.id,new_info)
    except Exception as e:
        err=type(e)
    finally:
        assert err==TypeError
