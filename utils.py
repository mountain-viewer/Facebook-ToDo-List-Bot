class Deadline:

  deadline_count = 0

  def __init__(self, name, deadline):
    Deadline.deadline_count += 1

    self.name = name
    self.deadline = deadline
    self.id = Deadline.deadline_count

  def __repr__(self):
    time_tuple = (self.deadline.tm_mday, self.deadline.tm_mon, self.deadline.tm_year)

    return "\n(" + "Title: " + self.name + "\n" +  "ID: "+ str(self.id) + "\n" + "Deadline: " + str(time_tuple) + ")\n"


class DeadlineCollection:

  def __init__(self):
    self.deadline_buffer = []

  def __len__(self):
    return len(self.deadline_buffer)

  def sort(self):
    self.deadline_buffer.sort(key=lambda x: x.deadline)

  def add(self, name, deadline):
    try:
      self.deadline_buffer.append(Deadline(name, deadline))
      return True
    except Exception:
      return False

  def remove(self, id):
    found_deadline = -1

    for i in range(len(self.deadline_buffer)):
      if self.deadline_buffer[i].id == id:
        found_deadline = i
        break

    if found_deadline != -1:
      del self.deadline_buffer[found_deadline]
      return True

    return False

  def list(self):
    return self.deadline_buffer

  def rename(self, id, new_name):
    for i in range(len(self.deadline_buffer)):
      if self.deadline_buffer[i].id == id:
        self.deadline_buffer[i].name = new_name
        return True

    return False

  def set_deadline(self, id, new_deadline):
    for i in range(len(self.deadline_buffer)):
      if self.deadline_buffer[i].id == id:
        self.deadline_buffer[i].deadline = new_deadline
        return True

    return False

  def done(self, id):
    found_deadline = -1

    for i in range(len(self.deadline_buffer)):
      if self.deadline_buffer[i].id == id:
        found_deadline = i

    if found_deadline != -1:
      del self.deadline_buffer[found_deadline]
      return True

    return False
