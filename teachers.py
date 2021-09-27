from bson.json_util import dumps
from bson.json_util import ObjectId

class Teachers():
  def __init__(self, lecturerCollection):
    self.lecturerCollection = lecturerCollection

  def addNewTeacher(self, obj):
    teacherId = self.lecturerCollection.insert(obj)
    teacher = self.lecturerCollection.find_one({'_id': ObjectId(teacherId)})
    teacher = dumps(teacher)

    return teacher

  def getTeacher(self, id):
    teacher = self.lecturerCollection.find_one({'_id': ObjectId(id)})
    teacher = dumps(teacher)
    
    
    return teacher

  def getTeacherByEmail(self, email):
    teacher = self.lecturerCollection.find_one({'email': email})
    teacher = dumps(teacher)   #not sure
   
    
    return teacher
