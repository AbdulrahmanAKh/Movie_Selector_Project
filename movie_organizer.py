import sys
import os
import sqlite3
import hashlib
from PyQt5 import QtWidgets, QtGui, QtCore, uic

# ---------------------------[ Database Manager ]--------------------------- #
class DatabaseManager:
    def __init__(self, db_name="movies.db"):
        self.conn = sqlite3.connect(db_name)

    def close(self):
        self.conn.close()

# ---------------------------[ Auth Manager ]--------------------------- #
class AuthManager:
    def __init__(self, db_conn):
        self.db = db_conn
        self.current_user_id = None
        self.fullname = None

    def hash_password(self, pw): 
        return hashlib.sha256(pw.encode()).hexdigest()

    def register_user(self, password, fullname, email, profile_pic):
        email_to_insert = email if email else None # to have option of not providing an email
        if email_to_insert:
            cur = self.db.execute("SELECT id FROM users WHERE email=?", (email_to_insert,))
            if cur.fetchone(): # fetch an existing email of the specified id if exist do
                return False, "Email already exists! Please use a different one."
        try:
            pw_to_insert = self.hash_password(password) if password else ""
            self.db.execute(
                "INSERT INTO users (password, fullname, email, profile_pic) VALUES (?,?,?,?)",
                (pw_to_insert, fullname, email_to_insert, profile_pic)
            )
            self.db.commit()
            return True, "Profile created successfully!"
        except sqlite3.IntegrityError as e:
            return False, str(e)

    def check_password(self, user_id, password):
        cur = self.db.execute("SELECT id, fullname, password FROM users WHERE id=?", (user_id,))
        row = cur.fetchone()
        if not row:
            return False, "User not found!"
        uid, fullname, pw_hash = row
        if pw_hash and self.hash_password(password) == pw_hash:
            self.current_user_id, self.fullname = uid, fullname
            return True, "Login successful!"
        return False, "Invalid password!"

    def login_without_password(self, user_id):
        cur = self.db.execute("SELECT id, fullname, password FROM users WHERE id=?", (user_id,))
        row = cur.fetchone()
        if not row:
            return False, "User not found!"
        uid, fullname, pw = row
        if not pw: # No password associated with the account
            self.current_user_id = uid
            self.fullname = fullname
            return True, "Login successful!"
        return False, "This profile requires a password!"

    def logout(self):
        self.current_user_id = None
        self.fullname = None

    def update_user(self, user_id, fullname, email, profile_pic, new_password_hash=None, remove_password=False):
        email_to_insert = email if email else None
        
        if email_to_insert: # email validation
            cur = self.db.execute("SELECT id FROM users WHERE email=? AND id != ?", (email_to_insert, user_id))
            if cur.fetchone():
                return False, "Email already exists on another profile!"

        try:
            if remove_password:
                self.db.execute(
                    "UPDATE users SET fullname=?, email=?, profile_pic=?, password='' WHERE id=?",
                    (fullname, email_to_insert, profile_pic, user_id)
                )
            elif new_password_hash is not None and new_password_hash != "":
                self.db.execute(
                    "UPDATE users SET fullname=?, email=?, profile_pic=?, password=? WHERE id=?",
                    (fullname, email_to_insert, profile_pic, new_password_hash, user_id)
                )
            else: # keep password as it is
                self.db.execute(
                    "UPDATE users SET fullname=?, email=?, profile_pic=? WHERE id=?",
                    (fullname, email_to_insert, profile_pic, user_id)
                )
            self.db.commit()
            return True, "Profile updated successfully!"
        except sqlite3.Error as e:
            return False, f"Database error: {e}"

    def remove_password(self, user_id):
        try:
            self.db.execute("UPDATE users SET password='' WHERE id=?", (user_id,))
            self.db.commit()
            return True, "Password removed successfully!"
        except sqlite3.Error as e:
            return False, f"Database error: {e}"

    def delete_user(self, user_id):
        try:
            self.db.execute("DELETE FROM movies WHERE user_id=?", (user_id,)) # delete all movies related to that user
            self.db.execute("DELETE FROM users WHERE id=?", (user_id,)) # delete all data related to that user
            self.db.commit()
            return True, "Profile and all associated movies deleted."
        except sqlite3.Error as e:
            self.db.rollback()
            return False, f"Database error: {e}"


# ---------------------------[ Helper Functions ]--------------------------- #
def browse_file(line_edit, parent, title="Select File"):
    path, _ = QtWidgets.QFileDialog.getOpenFileName(parent, title, "", "Images (*.png *.jpg *.jpeg *.bmp)")
    if path: line_edit.setText(path)

def show_warning(parent, msg): 
    QtWidgets.QMessageBox.warning(parent, "Error", msg)

# ---------------------------[ Register Dialog ]--------------------------- #
class RegisterDialog(QtWidgets.QDialog):
    def __init__(self, auth_manager):
        super().__init__()
        uic.loadUi("register.ui", self)
        self.auth = auth_manager
        self.browseBtn.clicked.connect(lambda: browse_file(self.profilePath, self)) # we use lambda to call browse_file func
        self.registerBtn.clicked.connect(self.register)                             # because .connect doesn't accept arguments
        self.backBtn.clicked.connect(self.reject)
    
    def register(self):
        full = self.fullnameEdit.text().strip()
        email = self.emailEdit.text().strip()
        pw = self.passwordEdit.text()
        conf = self.confirmEdit.text()
        pic = self.profilePath.text()

        if not full: # fullname is a required field
            return show_warning(self, "Please fill in Full Name!")
        if pw or conf: # password validation if provided
            if pw != conf:
                return show_warning(self, "Passwords do not match!")
            if len(pw) < 6:
                return show_warning(self, "Password must be at least 6 characters!")
        
        success, msg = self.auth.register_user(pw, full, email, pic)
        
        if success:
            QtWidgets.QMessageBox.information(self, "Success", msg)
            self.accept()
        else:
            show_warning(self, msg)

# ----------------------[ Edit Profile Dialog ]---------------------- #
class EditProfileDialog(QtWidgets.QDialog):
    def __init__(self, auth_manager, user_data):
        super().__init__()
        uic.loadUi("register.ui", self)
        self.auth = auth_manager
        self.user_data = user_data
        self.user_id = user_data["id"]

        self.setWindowTitle("Edit Profile")
        
        self.fullnameEdit.setText(user_data.get("fullname", "")) # uses .get because the data are dict, assigned in ClickableProfileCard
        self.emailEdit.setText(user_data.get("email", ""))
        self.profilePath.setText(user_data.get("profile_pic", ""))
        
        self.has_password = bool(user_data.get("password"))
        if self.has_password:
            self.passwordEdit.setPlaceholderText("New Password (leave blank to keep current)")
            self.confirmEdit.setPlaceholderText("Confirm New Password")
            
            self.removePassBtn = QtWidgets.QPushButton("Remove Password")
            self.removePassBtn.setObjectName("removePassBtn")
            self.removePassBtn.clicked.connect(self.remove_password)
            
            idx = self.verticalLayout.indexOf(self.confirmEdit)
            if idx != -1:
                self.verticalLayout.insertWidget(idx + 1, self.removePassBtn)
        else:
            self.passwordEdit.setPlaceholderText("Set Password (Optional, min. 6 characters)")
            self.confirmEdit.setPlaceholderText("Confirm Password")
        
        self.registerBtn.setText("Save Changes")
        self.registerBtn.clicked.connect(self.save_changes)
        self.backBtn.clicked.connect(self.reject)
        self.browseBtn.clicked.connect(lambda: browse_file(self.profilePath, self)) # pic browse for edit profile
        
        self.deleteBtn = QtWidgets.QPushButton("Delete Profile")
        # Set object name so it picks up the style from register.ui
        self.deleteBtn.setObjectName("deleteBtn") 
        self.deleteBtn.clicked.connect(self.delete_profile)
        
        # Add button to the layout named "buttonLayout" in the .ui file
        self.buttonLayout.insertWidget(0, self.deleteBtn)

    def remove_password(self):
        reply = QtWidgets.QMessageBox.question(
            self, 'Confirm Remove Password',
            f"Are you sure you want to remove the password for '{self.user_data['fullname']}'?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        if reply == QtWidgets.QMessageBox.Yes:
            full = self.fullnameEdit.text().strip()
            email = self.emailEdit.text().strip()
            pic = self.profilePath.text()
            if not full:
                return show_warning(self, "Full Name cannot be empty!")
            success, msg = self.auth.update_user(self.user_id, full, email, pic, remove_password=True)
            if success:
                self.user_data["password"] = ""
                QtWidgets.QMessageBox.information(self, "Success", "Password removed successfully!")
                self.accept()
            else:
                show_warning(self, msg)

    def delete_profile(self):
        reply = QtWidgets.QMessageBox.question(
            self, 'Confirm Delete',
            f"Are you sure you want to delete the profile '{self.user_data['fullname']}'?\nAll associated movies will be permanently deleted.",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            success, msg = self.auth.delete_user(self.user_id)
            if success:
                QtWidgets.QMessageBox.information(self, "Deleted", msg)
                self.accept()
            else:
                show_warning(self, msg)

    def save_changes(self):
        full = self.fullnameEdit.text().strip()
        email = self.emailEdit.text().strip()
        pic = self.profilePath.text()
        pw = self.passwordEdit.text()
        conf = self.confirmEdit.text()
        
        new_pass_hash = None
        
        if not full:
            return show_warning(self, "Full Name cannot be empty!")

        if pw or conf:
            if pw != conf:
                return show_warning(self, "Passwords do not match!")
            if len(pw) < 6:
                return show_warning(self, "Password must be at least 6 characters!")
            new_pass_hash = self.auth.hash_password(pw)
        
        success, msg = self.auth.update_user(self.user_id, full, email, pic, new_pass_hash)
        
        if success:
            QtWidgets.QMessageBox.information(self, "Success", msg)
            self.accept()
        else:
            show_warning(self, msg)

# ----------------------[ Password Entry Dialog ]---------------------- #
class PasswordEntryDialog(QtWidgets.QDialog):
    def __init__(self, auth_manager, user_id, fullname, profile_pic_path):
        super().__init__()

        uic.loadUi("password_entry.ui", self) 
        
        self.auth = auth_manager
        self.user_id = user_id
        
        # get profile pic from os
        self.nameLabel.setText(fullname)
        if profile_pic_path and os.path.exists(profile_pic_path):
            pix = QtGui.QPixmap(profile_pic_path).scaled(150, 150, QtCore.Qt.KeepAspectRatioByExpanding, QtCore.Qt.SmoothTransformation)
            self.picLabel.setPixmap(pix)
            self.picLabel.setText("") # Clear [No Pic] text
        
        self.unlockBtn.clicked.connect(self.check_pass)
        self.passwordEdit.returnPressed.connect(self.unlockBtn.click)

    def check_pass(self):
        password = self.passwordEdit.text()
        if not password:
            return show_warning(self, "Please enter a password.")
        
        success, msg = self.auth.check_password(self.user_id, password)
        if success:
            self.accept()
        else:
            show_warning(self, msg)
            self.passwordEdit.clear()

# ----------------------[ Confirm Login Dialog (No Password) ]---------------------- #
class ConfirmLoginDialog(QtWidgets.QDialog):
    def __init__(self, auth_manager, user_id, fullname, profile_pic_path):
        super().__init__()
        uic.loadUi("confirm_login.ui", self)
        self.auth = auth_manager
        self.user_id = user_id

        self.nameLabel.setText(fullname)
        if profile_pic_path and os.path.exists(profile_pic_path):
            pix = QtGui.QPixmap(profile_pic_path).scaled(150, 150, QtCore.Qt.KeepAspectRatioByExpanding, QtCore.Qt.SmoothTransformation)
            self.picLabel.setPixmap(pix)
            self.picLabel.setText("")
        
        self.continueBtn.clicked.connect(self.confirm_login)
        self.cancelBtn.clicked.connect(self.reject)
        self.continueBtn.setDefault(True)

    def confirm_login(self):
        success, msg = self.auth.login_without_password(self.user_id)
        if success:
            self.accept()
        else:
            show_warning(self, msg)

# ----------------------[ Clickable Profile Card ]---------------------- #
class ClickableProfileCard(QtWidgets.QFrame):
    clicked = QtCore.pyqtSignal(dict)
    editClicked = QtCore.pyqtSignal(dict)
    
    def __init__(self, user_data):
        super().__init__()
        self.user_data = user_data
        self.is_in_edit_mode = False
        self.normal_size = 130
        self.hover_size = 144
        
        # Set object name to pick up style from welcome.ui
        self.setObjectName("profileCard")
        self.setFixedSize(160, 210)
        self.setCursor(QtCore.Qt.PointingHandCursor)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignCenter)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # Outer container keeping card dimensions stable during avatar animation
        self.picContainer = QtWidgets.QWidget(self)
        self.picContainer.setFixedSize(150, 150)
        
        # Inner avatar frame that animates and scales (Netflix style)
        self.avatarBox = QtWidgets.QFrame(self.picContainer)
        self.avatarBox.setObjectName("avatarBox")
        offset = (150 - self.normal_size) // 2
        self.avatarBox.setGeometry(offset, offset, self.normal_size, self.normal_size)
        
        self.stackLayout = QtWidgets.QStackedLayout(self.avatarBox)
        self.stackLayout.setStackingMode(QtWidgets.QStackedLayout.StackAll)
        
        self.picLabel = QtWidgets.QLabel(self.avatarBox)
        self.picLabel.setObjectName("profilePic")
        self.picLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.picLabel.setScaledContents(True)
        self.updatePicture(user_data.get("profile_pic", ""))
        
        self.editOverlay = QtWidgets.QLabel("✏️", self.avatarBox)
        self.editOverlay.setObjectName("editOverlay")
        self.editOverlay.setAlignment(QtCore.Qt.AlignCenter)
        self.editOverlay.setVisible(False)
        
        self.stackLayout.addWidget(self.picLabel)
        self.stackLayout.addWidget(self.editOverlay)
        
        # Netflix-style glow / drop shadow
        self.shadow = QtWidgets.QGraphicsDropShadowEffect(self.avatarBox)
        self.shadow.setBlurRadius(15)
        self.shadow.setColor(QtGui.QColor(0, 0, 0, 160))
        self.shadow.setOffset(0, 4)
        self.avatarBox.setGraphicsEffect(self.shadow)
        
        layout.addWidget(self.picContainer, alignment=QtCore.Qt.AlignCenter)

        self.nameLabel = QtWidgets.QLabel(user_data["fullname"])
        self.nameLabel.setObjectName("profileName")
        self.nameLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.nameLabel.setWordWrap(True)
        layout.addWidget(self.nameLabel, alignment=QtCore.Qt.AlignCenter)
        
        # Smooth Netflix scale animation
        self.scaleAnim = QtCore.QPropertyAnimation(self.avatarBox, b"geometry")
        self.scaleAnim.setDuration(160)
        self.scaleAnim.setEasingCurve(QtCore.QEasingCurve.OutCubic)

    def updatePicture(self, path):
        if path and os.path.exists(path):
            pix = QtGui.QPixmap(path).scaled(150, 150, QtCore.Qt.KeepAspectRatioByExpanding, QtCore.Qt.SmoothTransformation)
            self.picLabel.setPixmap(pix)
            self.picLabel.setText("") # Clear [No Pic] text
        else:
            self.picLabel.setPixmap(QtGui.QPixmap()) # Clear pixmap
            self.picLabel.setText("[No Pic]")

    def enterEvent(self, e):
        self.scaleAnim.stop()
        hover_offset = (150 - self.hover_size) // 2
        self.scaleAnim.setStartValue(self.avatarBox.geometry())
        self.scaleAnim.setEndValue(QtCore.QRect(hover_offset, hover_offset, self.hover_size, self.hover_size))
        self.scaleAnim.start()
        
        self.avatarBox.setProperty("hovered", True)
        self.avatarBox.style().unpolish(self.avatarBox)
        self.avatarBox.style().polish(self.avatarBox)
        
        self.nameLabel.setProperty("hovered", True)
        self.nameLabel.style().unpolish(self.nameLabel)
        self.nameLabel.style().polish(self.nameLabel)
        
        self.shadow.setColor(QtGui.QColor(255, 255, 255, 90))
        self.shadow.setBlurRadius(25)
        super().enterEvent(e)

    def leaveEvent(self, e):
        self.scaleAnim.stop()
        normal_offset = (150 - self.normal_size) // 2
        self.scaleAnim.setStartValue(self.avatarBox.geometry())
        self.scaleAnim.setEndValue(QtCore.QRect(normal_offset, normal_offset, self.normal_size, self.normal_size))
        self.scaleAnim.start()
        
        self.avatarBox.setProperty("hovered", False)
        self.avatarBox.style().unpolish(self.avatarBox)
        self.avatarBox.style().polish(self.avatarBox)
        
        self.nameLabel.setProperty("hovered", False)
        self.nameLabel.style().unpolish(self.nameLabel)
        self.nameLabel.style().polish(self.nameLabel)
        
        self.shadow.setColor(QtGui.QColor(0, 0, 0, 160))
        self.shadow.setBlurRadius(15)
        super().leaveEvent(e)

    def setEditMode(self, is_edit):
        self.is_in_edit_mode = is_edit
        self.editOverlay.setVisible(is_edit)
        self.setCursor(QtCore.Qt.PointingHandCursor)

    def mousePressEvent(self, e):
        if self.is_in_edit_mode:
            self.editClicked.emit(self.user_data)
        else:
            self.clicked.emit(self.user_data)
        super().mousePressEvent(e)

# ---------------------[ Profile Selection Dialog ]--------------------- #
class ProfileSelectionDialog(QtWidgets.QDialog):
    def __init__(self, auth_manager, db_connection):
        super().__init__()
        uic.loadUi("welcome.ui", self)
        self.auth = auth_manager
        self.conn = db_connection
        self.is_edit_mode = False
        
        self.addProfileButton.clicked.connect(self.add_profile)
        self.editProfilesButton.clicked.connect(self.toggle_edit_mode)
        self.load_profiles()

    def load_profiles(self):
        while self.profileGrid.count():
            item = self.profileGrid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        cur = self.conn.execute("SELECT id, fullname, profile_pic, email, password FROM users")
        row, col = 0, 0
        for uid, fullname, profile_pic, email, password in cur:
            data = {"id": uid, "fullname": fullname, "profile_pic": profile_pic, "email": email, "password": password}
            card = ClickableProfileCard(data)
            
            card.clicked.connect(self.profile_clicked)
            card.editClicked.connect(self.profile_edit_clicked)
            
            card.setEditMode(self.is_edit_mode) 
            
            self.profileGrid.addWidget(card, row, col, QtCore.Qt.AlignCenter)
            col += 1
            if col > 3:
                col = 0
                row += 1
        
        # Add a spacer to push cards to the left
        self.profileGrid.addItem(QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum), 0, col, -1, -1)

    def toggle_edit_mode(self):
        self.is_edit_mode = not self.is_edit_mode
        
        if self.is_edit_mode:
            self.titleLabel.setText("Manage Profiles")
            self.editProfilesButton.setText("Done")
            self.addProfileButton.setVisible(False)
        else:
            self.titleLabel.setText("Who's watching?")
            self.editProfilesButton.setText("Edit Profiles")
            self.addProfileButton.setVisible(True)
            
        for i in range(self.profileGrid.count()):
            item = self.profileGrid.itemAt(i)
            widget = item.widget()
            if isinstance(widget, ClickableProfileCard):
                widget.setEditMode(self.is_edit_mode)

    def add_profile(self):
        dlg = RegisterDialog(self.auth)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            self.load_profiles()

    def profile_clicked(self, user_data):
        has_password = bool(user_data.get("password"))
        if has_password:
            dlg = PasswordEntryDialog(
                self.auth, 
                user_data["id"], 
                user_data["fullname"],
                user_data.get("profile_pic")
            )
        else:
            dlg = ConfirmLoginDialog(
                self.auth,
                user_data["id"],
                user_data["fullname"],
                user_data.get("profile_pic")
            )
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            self.accept()

    def profile_edit_clicked(self, user_data):
        dlg = EditProfileDialog(self.auth, user_data)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            self.load_profiles()


# ---------------------------[ Movie Card ]--------------------------- #
class ClickableMovieCard(QtWidgets.QFrame):
    clicked = QtCore.pyqtSignal(dict)
    def __init__(self, movie):
        super().__init__()
        self.movie_data = movie
        self.is_selected = False
        
        # Set object name to pick up style from movie_organizer.ui
        self.setObjectName("movieCard")
        self.setFixedSize(155, 235)
        self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.setCursor(QtCore.Qt.PointingHandCursor)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignTop)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        
        # Poster container with stacked layout for interactive play overlay
        self.posterContainer = QtWidgets.QFrame(self)
        self.posterContainer.setFixedSize(139, 168)
        self.posterLayout = QtWidgets.QStackedLayout(self.posterContainer)
        self.posterLayout.setStackingMode(QtWidgets.QStackedLayout.StackAll)
        
        self.poster_label = QtWidgets.QLabel(self.posterContainer)
        self.poster_label.setObjectName("moviePoster")
        self.poster_label.setAlignment(QtCore.Qt.AlignCenter)
        self.poster_label.setScaledContents(True)
        self.updatePoster()
        
        self.playOverlay = QtWidgets.QLabel("▶", self.posterContainer)
        self.playOverlay.setObjectName("playOverlay")
        self.playOverlay.setAlignment(QtCore.Qt.AlignCenter)
        self.playOverlay.setVisible(False)
        
        self.posterLayout.addWidget(self.poster_label)
        self.posterLayout.addWidget(self.playOverlay)
        layout.addWidget(self.posterContainer)
        
        self.title_label = QtWidgets.QLabel(movie["title"])
        self.title_label.setObjectName("movieTitle")
        self.title_label.setAlignment(QtCore.Qt.AlignCenter)
        self.title_label.setWordWrap(True)
        
        self.rating_label = QtWidgets.QLabel(f"⭐ {movie['rating']}")
        self.rating_label.setObjectName("movieRating")
        self.rating_label.setAlignment(QtCore.Qt.AlignCenter)
        
        layout.addWidget(self.title_label)
        layout.addWidget(self.rating_label)
        layout.addStretch()

        # Drop shadow effect for interactive depth
        self.shadow = QtWidgets.QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(12)
        self.shadow.setOffset(0, 3)
        self.shadow.setColor(QtGui.QColor(0, 0, 0, 140))
        self.setGraphicsEffect(self.shadow)

        self.setToolTip(f"{movie['title']} ({movie.get('year', '')})\nGenre: {movie.get('genre', '')}\nRating: ⭐ {movie.get('rating', '')}")

    def updatePoster(self):
        path = self.movie_data.get("poster","")
        if path and os.path.exists(path):
            pix = QtGui.QPixmap(path).scaled(140, 170, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            self.poster_label.setPixmap(pix)
            self.poster_label.setText("")
        else:
            self.poster_label.setPixmap(QtGui.QPixmap())
            self.poster_label.setText("[Poster]")

    def enterEvent(self, e):
        self.playOverlay.setVisible(True)
        if not self.is_selected:
            self.shadow.setColor(QtGui.QColor(229, 9, 20, 140)) # Netflix red ambient glow
            self.shadow.setBlurRadius(24)
            self.shadow.setOffset(0, 6)
        super().enterEvent(e)

    def leaveEvent(self, e):
        self.playOverlay.setVisible(False)
        if not self.is_selected:
            self.shadow.setColor(QtGui.QColor(0, 0, 0, 140))
            self.shadow.setBlurRadius(12)
            self.shadow.setOffset(0, 3)
        else:
            self.shadow.setColor(QtGui.QColor(245, 197, 24, 180)) # Gold glow when selected
            self.shadow.setBlurRadius(20)
            self.shadow.setOffset(0, 4)
        super().leaveEvent(e)

    def setSelected(self, selected):
        self.is_selected = selected
        self.setProperty("selected", selected)
        if selected:
            self.shadow.setColor(QtGui.QColor(245, 197, 24, 180)) # Gold glow
            self.shadow.setBlurRadius(22)
            self.shadow.setOffset(0, 4)
        else:
            self.shadow.setColor(QtGui.QColor(0, 0, 0, 140))
            self.shadow.setBlurRadius(12)
            self.shadow.setOffset(0, 3)
        self.style().unpolish(self)
        self.style().polish(self)

    def mousePressEvent(self, e): 
        self.clicked.emit(self.movie_data)
        super().mousePressEvent(e)

# ---------------------------[ Add/Edit Movie Dialog ]--------------------------- #
class AddMovieDialog(QtWidgets.QDialog):
    def __init__(self,parent=None,movie=None):
        super().__init__(parent)
        uic.loadUi("add_movie.ui", self)
        self.movie = movie
        self.browseBtn.clicked.connect(lambda: browse_file(self.posterPath,self))
        self.cancelBtn.clicked.connect(self.reject)
        self.saveBtn.clicked.connect(self.accept)
        if movie:
            self.setWindowTitle("Edit Movie")
            self.titleEdit.setText(movie["title"])
            self.genreEdit.setText(movie["genre"])
            self.yearSpin.setValue(movie["year"])
            self.ratingSpin.setValue(movie["rating"])
            self.posterPath.setText(movie["poster"])
            
    def get_data(self):
        return {
            "title": self.titleEdit.text(),
            "genre": self.genreEdit.text(),
            "year": self.yearSpin.value(),
            "rating": self.ratingSpin.value(),
            "poster": self.posterPath.text()
        }

# ---------------------------[ Main Window ]--------------------------- #
class MovieCarousel(QtWidgets.QMainWindow):
    def __init__(self, auth, db_manager):
        super().__init__()
        uic.loadUi("movie_organizer.ui", self)
        self.auth = auth; self.conn = db_manager.conn
        self.selected_movie_id = None

        self.addButton.clicked.connect(self.add_movie_dialog)
        self.editButton.clicked.connect(self.edit_selected)
        self.deleteButton.clicked.connect(self.delete_movie)
        self.searchEdit.textChanged.connect(self.load_movies)
        self.sortCombo.addItems(["Title (A-Z)","Year (Newest)","Year (Oldest)","Rating (High-Low)","Rating (Low-High)"])
        self.sortCombo.currentTextChanged.connect(self.load_movies)
        self.genreCombo.currentTextChanged.connect(self.load_movies)
        
        self.setWindowTitle(f"Movie Collection - {self.auth.fullname}")
        self.load_movies()

    def get_unique_genres(self): # sperates the genre " - " from the database and add it to the dropdown combo box
        genres=set()
        cur=self.conn.execute("SELECT DISTINCT genre FROM movies WHERE user_id=?",(self.auth.current_user_id,))
        for (g,) in cur:
            if g: genres.update([x.strip() for x in g.split(' - ')])
        return sorted(list(genres))

    def populate_genre_combo(self):
        self.genreCombo.blockSignals(True)
        cur_text=self.genreCombo.currentText()
        self.genreCombo.clear(); self.genreCombo.addItem("All Genres"); self.genreCombo.addItems(self.get_unique_genres())
        idx=self.genreCombo.findText(cur_text); self.genreCombo.setCurrentIndex(idx if idx!=-1 else 0)
        self.genreCombo.blockSignals(False)

    def load_movies(self):
        # Clear layout
        while self.carouselLayout.count() > 1: # Keep the spacer
            item = self.carouselLayout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
                
        self.selected_movie_id=None; self.movieDetailsLabel.setText("Select a movie to view details")
        self.populate_genre_combo()
        search='%'+self.searchEdit.text()+'%'; genre=self.genreCombo.currentText()
        sort_map={"Title (A-Z)":"title ASC","Year (Newest)":"year DESC","Year (Oldest)":"year ASC",
                  "Rating (High-Low)":"rating DESC","Rating (Low-High)":"rating ASC"}
        sort=sort_map.get(self.sortCombo.currentText(),"")
        query="SELECT id,title,genre,year,rating,poster FROM movies WHERE user_id=? AND title LIKE ?"
        params=[self.auth.current_user_id,search]
        
        if genre!="All Genres": query+=" AND genre LIKE '%'||?||'%'"; params.append(genre)
        if sort: query+=" ORDER BY "+sort
        
        for mid,title,genre,year,rating,poster in self.conn.execute(query,params):
            data={"id":mid,"title":title,"genre":genre,"year":year,"rating":rating,"poster":poster}
            card=ClickableMovieCard(data)
            card.clicked.connect(self.movie_selected)
            # Insert card before the spacer
            self.carouselLayout.insertWidget(self.carouselLayout.count()-1, card) 

    def add_movie_dialog(self):
        dlg=AddMovieDialog(self)
        if dlg.exec_()==QtWidgets.QDialog.Accepted:
            d=dlg.get_data()
            self.conn.execute("INSERT INTO movies(title,genre,year,rating,poster,user_id) VALUES (?,?,?,?,?,?)",
                              (d["title"],d["genre"],d["year"],d["rating"],d["poster"],self.auth.current_user_id))
            self.conn.commit(); self.load_movies()

    def edit_selected(self):
        if not self.selected_movie_id: return QtWidgets.QMessageBox.information(self,"Select","Select a movie first.")
        cur=self.conn.execute("SELECT * FROM movies WHERE id=?",(self.selected_movie_id,)).fetchone()
        if not cur: return
        movie={"id":cur[0],"title":cur[1],"genre":cur[2],"year":cur[3],"rating":cur[4],"poster":cur[5]}
        dlg=AddMovieDialog(self,movie)
        if dlg.exec_()==QtWidgets.QDialog.Accepted:
            d=dlg.get_data()
            self.conn.execute("UPDATE movies SET title=?,genre=?,year=?,rating=?,poster=? WHERE id=?",
                              (d["title"],d["genre"],d["year"],d["rating"],d["poster"],movie["id"]))
            self.conn.commit(); self.load_movies()

    def delete_movie(self):
        if not self.selected_movie_id: return QtWidgets.QMessageBox.information(self,"Select","Select a movie first.")
        reply=QtWidgets.QMessageBox.question(self,'Confirm Delete',"Are you sure?",QtWidgets.QMessageBox.Yes|QtWidgets.QMessageBox.No,QtWidgets.QMessageBox.No)
        if reply==QtWidgets.QMessageBox.Yes:
            self.conn.execute("DELETE FROM movies WHERE id=?",(self.selected_movie_id,))
            self.conn.commit(); self.selected_movie_id=None; self.movieDetailsLabel.setText("Select a movie to view details"); self.load_movies()

    def movie_selected(self,movie):
        self.selected_movie_id=movie["id"]
        self.movieDetailsLabel.setText(f"<b>{movie['title']}</b> ({movie['year']})<br>Genre: {movie['genre']}<br>Rating: ⭐ <b>{movie['rating']}</b>")

        # Update selection state and interactive effects
        for i in range(self.carouselLayout.count()):
            w=self.carouselLayout.itemAt(i).widget()
            if isinstance(w,ClickableMovieCard):
                is_selected = (w.movie_data["id"] == movie["id"])
                w.setSelected(is_selected)

# ---------------------------[ MAIN ]--------------------------- #
def main():
    app = QtWidgets.QApplication(sys.argv)
    
    # this is a global stylesheet for QMessageBox pop-ups texts & background
    app.setStyleSheet("""
        QMessageBox {
            background-color: #2b2b2b;
            border: 1px solid #555;
        }
        QMessageBox QLabel {
            color: white;
            font-size: 14px;
        }
        QMessageBox QPushButton {
            background-color: #555;
            color: white;
            border-radius: 8px;
            padding: 8px;
            min-width: 80px;
        }
        QMessageBox QPushButton:hover {
            background-color: #666;
        }
    """)
    
    db = DatabaseManager()
    auth = AuthManager(db.conn)
    
    while True:
        auth.logout()
        profile_selector = ProfileSelectionDialog(auth, db.conn)
        
        if profile_selector.exec_() == QtWidgets.QDialog.Accepted:
            w = MovieCarousel(auth, db)
            w.show()
            app.exec_()
        else:
            break
        
    db.close()
    sys.exit(0)

if __name__=="__main__":
    main()

