import sys
import os
import re
import json
import shutil
import io
import tokenize
from pathlib import Path
from typing import Dict ,List ,Optional ,Set ,Tuple
from datetime import datetime
from PyQt6 .QtWidgets import (
QApplication ,QMainWindow ,QWidget ,QVBoxLayout ,QHBoxLayout ,
QTreeWidget ,QTreeWidgetItem ,QPushButton ,QLabel ,QCheckBox ,
QFileDialog ,QMessageBox ,QGroupBox ,QScrollArea ,QTextEdit ,
QSplitter ,QHeaderView ,QTabWidget ,QTableWidget ,QTableWidgetItem ,
QProgressBar ,QLineEdit ,QComboBox ,QSpinBox ,QDoubleSpinBox ,
QListWidget ,QListWidgetItem ,QDialog ,QDialogButtonBox ,QInputDialog
)
from PyQt6 .QtCore import Qt ,QDir ,QThread ,QTimer ,pyqtSignal
from PyQt6 .QtGui import QIcon ,QFont ,QKeySequence ,QShortcut
_TREE_SITTER_JS_LANGUAGE =None
_TREE_SITTER_JS_PARSER =None
_TREE_SITTER_JS_INIT_ATTEMPTED =False
_TREE_SITTER_TS_LANGUAGE =None
_TREE_SITTER_TSX_LANGUAGE =None
_TREE_SITTER_TS_PARSER =None
_TREE_SITTER_TSX_PARSER =None
_TREE_SITTER_TS_INIT_ATTEMPTED =False
_TREE_SITTER_JS_PATH =Path (os .environ .get ('TEMP',''))/'codex_treesitter'
class ProjectStatisticsWorker (QThread ):
    stats_ready =pyqtSignal (str ,dict )
    def __init__ (self ,project_token :str ,file_infos :List [Dict ],calculator ,parent =None ):
        super ().__init__ (parent )
        self .project_token =project_token
        self .file_infos =file_infos
        self .calculator =calculator
    def run (self ):
        stats =self .calculator (self .file_infos ,self )
        if not self .isInterruptionRequested ():
            self .stats_ready .emit (self .project_token ,stats )
class CodeCleanerApp (QMainWindow ):
    PATH_ROLE =int (Qt .ItemDataRole .UserRole )
    IS_DIR_ROLE =PATH_ROLE +1
    IS_CODE_FILE_ROLE =PATH_ROLE +2
    def __init__ (self ):
        super ().__init__ ()
        self .project_path =None
        self .project_index_ready =False
        self .project_tree_data =[]
        self .project_file_infos =[]
        self .code_file_infos =[]
        self .stats_worker =None
        self .file_extensions ={
        '.py':'Python',
        '.js':'JavaScript',
        '.ts':'TypeScript',
        '.java':'Java',
        '.cpp':'C++',
        '.c':'C',
        '.h':'Заголовок C/C++',
        '.hpp':'Заголовок С++',
        '.ino':'Arduino',
        '.cs':'C#',
        '.php':'PHP',
        '.rb':'Ruby',
        '.go':'Go',
        '.rs':'Rust',
        '.swift':'Swift',
        '.kt':'Kotlin',
        '.scala':'Scala',
        '.r':'R',
        '.m':'Objective-C',
        '.sql':'SQL',
        '.html':'HTML',
        '.css':'CSS',
        '.scss':'SCSS',
        '.vue':'Vue',
        '.jsx':'JSX',
        '.tsx':'TSX',
        '.xml':'XML',
        '.json':'JSON',
        '.yaml':'YAML',
        '.yml':'YAML',
        '.sh':'Shell',
        '.bat':'Batch',
        '.ps1':'PowerShell',
        '.md':'Markdown',
        }
        self .detected_languages =set ()
        self .file_backups ={}
        self .history =[]
        self .settings_profiles ={}
        self .current_profile ="default"
        self .settings_file =Path .home ()/".code_cleaner_settings.json"
        self .history_file =Path .home ()/".code_cleaner_history.json"
        self .load_settings ()
        self .init_ui ()
        QTimer .singleShot (0 ,self ._finish_startup )
    def init_ui (self ):
        self .setWindowTitle ('Code Cleaner - Очистка кода от комментариев')
        self .setGeometry (100 ,100 ,1400 ,800 )
        self .setStyleSheet ("""            QMainWindow {
                            цвет фона:
                        }
                        QВиджет {
                            цвет фона:
                            цвет:
                        }
                        QTreeWidget {
                            цвет фона:
                            цвет:
                            граница: сплошная 1 пиксель
                            выбор-фонового цвета:
                        }
                        QКнопка {
                            цвет фона:
                            цвет: белый;
                            граница: нет;
                            отступы: 8 пикселей 16 пикселей;
                            радиус границы: 4 пикселя;
                            размер шрифта: 12 пикселей;
                        }
                        QPushButton: напишите {
                            цвет фона:
                        }
                        QPushButton: нажал {
                            цвет фона:
                        }
                        QPushButton: отключено {
                            цвет фона:
                            цвет:
                        }
                        QGroupBox {
                            граница: сплошная 1 пиксель
                            радиус границы: 4 пикселя;
                            маржа сверху: 10 пикселей;
                            отступ сверху: 10 пикселей;
                            начертание шрифта: жирный;
                        }
                        QGroupBox::title {
                            subcontrol-origin: маржа;
                            слева: 10 пикселей;
                            отступ: 0 5 пикселей;
                        }
                        QCheckBox {
                            цвет:
                            интервал: 5 пикселей;
                        }
                        QCheckBox::индикатор {
                            ширина: 18 пикселей;
                            высота: 18 пикселей;
                            граница: сплошная 2 пикселя
                            радиус границы: 3 пикселя;
                            цвет фона:
                        }
                        QCheckBox::indicator:checked {
                            цвет фона:
                            цвет границы:
                        }
                        QLabel {
                            цвет:
                        }
                        QScrollArea {
                            граница: нет;
                            цвет фона:
                        }
                        QTextEdit {
                            цвет фона:
                            цвет:
                            граница: сплошная 1 пиксель
                        }""")
        central_widget =QWidget ()
        self .setCentralWidget (central_widget )
        main_layout =QHBoxLayout (central_widget )
        main_layout .setContentsMargins (10 ,10 ,10 ,10 )
        main_layout .setSpacing (10 )
        splitter =QSplitter (Qt .Orientation .Horizontal )
        main_layout .addWidget (splitter )
        left_panel =QWidget ()
        left_layout =QVBoxLayout (left_panel )
        left_layout .setContentsMargins (0 ,0 ,0 ,0 )
        self .open_folder_btn =QPushButton ('📁 Открыть папку проекта')
        self .open_folder_btn .clicked .connect (self .open_folder )
        left_layout .addWidget (self .open_folder_btn )
        self .file_tree =QTreeWidget ()
        self .file_tree .setHeaderLabel ('Файлы проекта')
        self .file_tree .setRootIsDecorated (True )
        self .file_tree .itemChanged .connect (self .on_item_changed )
        left_layout .addWidget (self .file_tree )
        splitter .addWidget (left_panel )
        self .tabs =QTabWidget ()
        self .tabs .setStyleSheet ("""
            QTabWidget::pane {
                border: 1px solid
                background-color:
            }
            QTabBar::tab {
                background-color:
                color:
                padding: 8px 16px;
                border: 1px solid
                border-bottom: none;
            }
            QTabBar::tab:selected {
                background-color:
                color: white;
            }
            QTabBar::tab:hover {
                background-color:
            }
        """)
        self .main_tab =self .create_main_tab ()
        self .tabs .addTab (self .main_tab ,"⚙️ Настройки")
        self .stats_tab =self .create_stats_tab ()
        self .tabs .addTab (self .stats_tab ,"📊 Статистика")
        self .settings_tab =self .create_settings_tab ()
        self .tabs .addTab (self .settings_tab ,"🔧 Профили")
        self .history_tab =self .create_history_tab ()
        self .tabs .addTab (self .history_tab ,"📜 История")
        splitter .addWidget (self .tabs )
        splitter .setSizes ([600 ,400 ])
        self .setup_shortcuts ()
        if self .current_profile in self .settings_profiles :
            self .load_profile (self .current_profile )
    def _finish_startup (self ):
        try :
            self .load_history ()
        except Exception :
            self .history =[]
    def create_main_tab (self ):
        tab =QWidget ()
        layout =QVBoxLayout (tab )
        layout .setContentsMargins (10 ,10 ,10 ,10 )
        scroll =QScrollArea ()
        scroll .setWidgetResizable (True )
        scroll .setHorizontalScrollBarPolicy (Qt .ScrollBarPolicy .ScrollBarAlwaysOff )
        content =QWidget ()
        content_layout =QVBoxLayout (content )
        info_group =QGroupBox ('Информация о проекте')
        info_layout =QVBoxLayout ()
        self .project_label =QLabel ('Проект не выбран')
        self .languages_label =QLabel ('Языки: не определены')
        info_layout .addWidget (self .project_label )
        info_layout .addWidget (self .languages_label )
        info_group .setLayout (info_layout )
        content_layout .addWidget (info_group )
        options_group =QGroupBox ('Опции очистки')
        options_layout =QVBoxLayout ()
        self .remove_comments_cb =QCheckBox ('Удалить комментарии')
        self .remove_empty_lines_cb =QCheckBox ('Удалить пустые строки')
        self .verify_code_cb =QCheckBox ('Проверить код после выполнения')
        self .create_resources_cb =QCheckBox ('Создать requirements.txt (Python)')
        options_layout .addWidget (self .remove_comments_cb )
        options_layout .addWidget (self .remove_empty_lines_cb )
        options_layout .addWidget (self .verify_code_cb )
        options_layout .addWidget (self .create_resources_cb )
        options_group .setLayout (options_layout )
        content_layout .addWidget (options_group )
        extra_group =QGroupBox ('Дополнительные функции')
        extra_layout =QVBoxLayout ()
        self .remove_trailing_spaces_cb =QCheckBox ('Удалить пробелы в конце строк')
        self .normalize_line_endings_cb =QCheckBox ('Нормализовать окончания строк (LF)')
        self .backup_files_cb =QCheckBox ('Создать резервные копии')
        extra_layout .addWidget (self .remove_trailing_spaces_cb )
        extra_layout .addWidget (self .normalize_line_endings_cb )
        extra_layout .addWidget (self .backup_files_cb )
        extra_group .setLayout (extra_layout )
        content_layout .addWidget (extra_group )
        actions_group =QGroupBox ('Действия')
        actions_layout =QVBoxLayout ()
        self .process_btn =QPushButton ('🚀 Обработать выбранные файлы')
        self .process_btn .clicked .connect (self .process_files )
        self .process_btn .setEnabled (False )
        self .delete_file_btn =QPushButton ('🗑️ Удалить выбранные файлы')
        self .delete_file_btn .clicked .connect (self .delete_selected_files )
        self .delete_file_btn .setEnabled (False )
        self .select_all_btn =QPushButton ('✓ Выбрать все')
        self .select_all_btn .clicked .connect (self .select_all_files )
        self .deselect_all_btn =QPushButton ('✗ Снять выделение')
        self .deselect_all_btn .clicked .connect (self .deselect_all_files )
        actions_layout .addWidget (self .process_btn )
        actions_layout .addWidget (self .delete_file_btn )
        actions_layout .addWidget (self .select_all_btn )
        actions_layout .addWidget (self .deselect_all_btn )
        actions_group .setLayout (actions_layout )
        content_layout .addWidget (actions_group )
        log_group =QGroupBox ('Лог операций')
        log_layout =QVBoxLayout ()
        self .progress_bar =QProgressBar ()
        self .progress_bar .setVisible (False )
        log_layout .addWidget (self .progress_bar )
        self .log_text =QTextEdit ()
        self .log_text .setReadOnly (True )
        self .log_text .setMaximumHeight (200 )
        log_layout .addWidget (self .log_text )
        log_group .setLayout (log_layout )
        content_layout .addWidget (log_group )
        content_layout .addStretch ()
        scroll .setWidget (content )
        layout .addWidget (scroll )
        return tab
    def create_stats_tab (self ):
        tab =QWidget ()
        layout =QVBoxLayout (tab )
        layout .setContentsMargins (10 ,10 ,10 ,10 )
        refresh_btn =QPushButton ('🔄 Обновить статистику')
        refresh_btn .clicked .connect (self .update_statistics )
        layout .addWidget (refresh_btn )
        self .stats_table =QTableWidget ()
        self .stats_table .setColumnCount (2 )
        self .stats_table .setHorizontalHeaderLabels (['Параметр','Значение'])
        self .stats_table .horizontalHeader ().setStretchLastSection (True )
        self .stats_table .setAlternatingRowColors (True )
        self .stats_table .setStyleSheet ("""
            QTableWidget {
                background-color:
                color:
                gridline-color:
            }
            QHeaderView::section {
                background-color:
                color: white;
                padding: 5px;
                border: none;
            }
        """)
        layout .addWidget (self .stats_table )
        return tab
    def create_settings_tab (self ):
        tab =QWidget ()
        layout =QVBoxLayout (tab )
        layout .setContentsMargins (10 ,10 ,10 ,10 )
        profile_group =QGroupBox ('Профили настроек')
        profile_layout =QVBoxLayout ()
        profile_hbox =QHBoxLayout ()
        self .profile_combo =QComboBox ()
        self .profile_combo .addItems (list (self .settings_profiles .keys ())if self .settings_profiles else ['default'])
        self .profile_combo .currentTextChanged .connect (self .load_profile )
        profile_hbox .addWidget (QLabel ('Текущий профиль:'))
        profile_hbox .addWidget (self .profile_combo )
        new_profile_btn =QPushButton ('➕ Новый')
        new_profile_btn .clicked .connect (self .create_new_profile )
        profile_hbox .addWidget (new_profile_btn )
        delete_profile_btn =QPushButton ('🗑️ Удалить')
        delete_profile_btn .clicked .connect (self .delete_profile )
        profile_hbox .addWidget (delete_profile_btn )
        profile_layout .addLayout (profile_hbox )
        save_btn =QPushButton ('💾 Сохранить текущие настройки')
        save_btn .clicked .connect (self .save_current_profile )
        profile_layout .addWidget (save_btn )
        export_btn =QPushButton ('📤 Экспорт профиля')
        export_btn .clicked .connect (self .export_profile )
        profile_layout .addWidget (export_btn )
        import_btn =QPushButton ('📥 Импорт профиля')
        import_btn .clicked .connect (self .import_profile )
        profile_layout .addWidget (import_btn )
        profile_group .setLayout (profile_layout )
        layout .addWidget (profile_group )
        shortcuts_group =QGroupBox ('Горячие клавиши')
        shortcuts_layout =QVBoxLayout ()
        shortcuts_info =QLabel (
        "Ctrl+O - Открыть папку\n"
        "Ctrl+A - Выбрать все файлы\n"
        "Ctrl+D - Снять выделение\n"
        "Ctrl+R - Обработать файлы\n"
        "Ctrl+S - Сохранить профиль\n"
        "F5 - Обновить статистику"
        )
        shortcuts_layout .addWidget (shortcuts_info )
        shortcuts_group .setLayout (shortcuts_layout )
        layout .addWidget (shortcuts_group )
        layout .addStretch ()
        return tab
    def create_history_tab (self ):
        tab =QWidget ()
        layout =QVBoxLayout (tab )
        layout .setContentsMargins (10 ,10 ,10 ,10 )
        history_controls =QHBoxLayout ()
        refresh_history_btn =QPushButton ('🔄 Обновить')
        refresh_history_btn .clicked .connect (self .refresh_history )
        history_controls .addWidget (refresh_history_btn )
        clear_history_btn =QPushButton ('🗑️ Очистить')
        clear_history_btn .clicked .connect (self .clear_history )
        history_controls .addWidget (clear_history_btn )
        layout .addLayout (history_controls )
        self .history_list =QListWidget ()
        self .history_list .setStyleSheet ("""
            QListWidget {
                background-color:
                color:
                border: 1px solid
            }
            QListWidget::item:selected {
                background-color:
            }
        """)
        self .history_list .itemDoubleClicked .connect (self .restore_from_history )
        layout .addWidget (self .history_list )
        restore_btn =QPushButton ('↩️ Восстановить выбранную версию')
        restore_btn .clicked .connect (self .restore_from_history )
        layout .addWidget (restore_btn )
        return tab
    def open_folder (self ):
        folder =QFileDialog .getExistingDirectory (self ,'Выберите папку проекта')
        if folder :
            self .project_path =Path (folder )
            self .invalidate_project_cache ()
            self .project_label .setText (f'Проект: {self .project_path .name }')
            self .load_project_files ()
            self .detect_languages ()
            self .update_statistics ()
            self .log (f'Открыт проект: {self .project_path }')
    def invalidate_project_cache (self ):
        self .project_index_ready =False
        self .project_tree_data =[]
        self .project_file_infos =[]
        self .code_file_infos =[]
    def ensure_project_index (self ,force :bool =False ):
        if not self .project_path :
            self .invalidate_project_cache ()
            return
        if self .project_index_ready and not force :
            return
        self .detected_languages =set ()
        self .project_file_infos =[]
        self .code_file_infos =[]
        self .project_tree_data =self ._scan_directory (self .project_path )
        self .project_index_ready =True
    def _scan_directory (self ,path :Path ):
        visible_entries =[]
        scanned_entries =[]
        try :
            with os .scandir (path )as iterator :
                for entry in iterator :
                    try :
                        is_dir =entry .is_dir (follow_symlinks =False )
                    except (OSError ,PermissionError ):
                        continue
                    scanned_entries .append ((not is_dir ,entry .name .lower (),entry ,is_dir ))
        except (OSError ,PermissionError ):
            return visible_entries
        scanned_entries .sort (key =lambda item :(item [0 ],item [1 ]))
        for _sort_key ,_name_key ,entry ,is_dir in scanned_entries :
            entry_path =Path (entry .path )
            is_visible_in_tree =not entry .name .startswith ('.')or entry .name =='.git'
            if is_dir :
                children =self ._scan_directory (entry_path )
                if is_visible_in_tree :
                    visible_entries .append ({
                    'name':entry .name ,
                    'display_name':entry .name ,
                    'path':entry_path ,
                    'is_dir':True ,
                    'is_code_file':False ,
                    'children':children ,
                    })
                continue
            ext =entry_path .suffix .lower ()
            is_code_file =ext in self .file_extensions
            language =self .file_extensions .get (ext )
            try :
                size =entry .stat (follow_symlinks =False ).st_size
            except (OSError ,PermissionError ):
                size =0
            file_info ={
            'name':entry .name ,
            'display_name':f'{entry .name } ({language })'if is_code_file else entry .name ,
            'path':entry_path ,
            'ext':ext ,
            'language':language ,
            'is_dir':False ,
            'is_code_file':is_code_file ,
            'size':size ,
            }
            self .project_file_infos .append (file_info )
            if is_code_file :
                self .code_file_infos .append (file_info )
                self .detected_languages .add (language )
            if is_visible_in_tree :
                visible_entries .append (file_info )
        return visible_entries
    def load_project_files (self ):
        self .file_tree .clear ()
        if not self .project_path :
            return
        self .ensure_project_index ()
        self .file_tree .blockSignals (True )
        self .file_tree .setUpdatesEnabled (False )
        root_item =QTreeWidgetItem (self .file_tree )
        root_item .setText (0 ,self .project_path .name )
        root_item .setCheckState (0 ,Qt .CheckState .Unchecked )
        root_item .setData (0 ,self .PATH_ROLE ,str (self .project_path ))
        root_item .setData (0 ,self .IS_DIR_ROLE ,True )
        root_item .setData (0 ,self .IS_CODE_FILE_ROLE ,False )
        self ._add_tree_nodes (root_item ,self .project_tree_data )
        self .file_tree .expandAll ()
        self .file_tree .setUpdatesEnabled (True )
        self .file_tree .blockSignals (False )
    def _add_tree_nodes (self ,parent_item ,entries ):
        for entry in entries :
            child_item =QTreeWidgetItem (parent_item )
            child_item .setText (0 ,entry ['display_name'])
            child_item .setCheckState (0 ,Qt .CheckState .Unchecked )
            child_item .setData (0 ,self .PATH_ROLE ,str (entry ['path']))
            child_item .setData (0 ,self .IS_DIR_ROLE ,entry ['is_dir'])
            child_item .setData (0 ,self .IS_CODE_FILE_ROLE ,entry .get ('is_code_file',False ))
            if entry ['is_dir']:
                child_item .setChildIndicatorPolicy (QTreeWidgetItem .ChildIndicatorPolicy .ShowIndicator )
                self ._add_tree_nodes (child_item ,entry .get ('children',[]))
    def on_item_changed (self ,item ,column ):
        if item .data (0 ,self .IS_DIR_ROLE ):
            new_state =item .checkState (0 )
            self .file_tree .blockSignals (True )
            self ._set_children_state (item ,new_state )
            self .file_tree .blockSignals (False )
        has_selected =self .has_selected_files ()
        self .process_btn .setEnabled (has_selected )
        self .delete_file_btn .setEnabled (has_selected )
    def _set_children_state (self ,parent_item ,state ):
        for i in range (parent_item .childCount ()):
            child =parent_item .child (i )
            child .setCheckState (0 ,state )
            if child .data (0 ,self .IS_DIR_ROLE ):
                self ._set_children_state (child ,state )
    def has_selected_files (self ):
        def check_item (item ):
            if item .checkState (0 )==Qt .CheckState .Checked and item .data (0 ,self .IS_CODE_FILE_ROLE ):
                return True
            for i in range (item .childCount ()):
                if check_item (item .child (i )):
                    return True
            return False
        for i in range (self .file_tree .topLevelItemCount ()):
            if check_item (self .file_tree .topLevelItem (i )):
                return True
        return False
    def get_selected_files (self ):
        selected =[]
        def collect_files (item ):
            if item .checkState (0 )==Qt .CheckState .Checked and item .data (0 ,self .IS_CODE_FILE_ROLE ):
                selected .append (Path (item .data (0 ,self .PATH_ROLE )))
            for i in range (item .childCount ()):
                collect_files (item .child (i ))
        for i in range (self .file_tree .topLevelItemCount ()):
            collect_files (self .file_tree .topLevelItem (i ))
        return selected
    def detect_languages (self ):
        self .detected_languages =set ()
        if not self .project_path :
            return
        for file_path in self .project_path .rglob ('*'):
            if file_path .is_file ():
                ext =file_path .suffix .lower ()
                if ext in self .file_extensions :
                    self .detected_languages .add (self .file_extensions [ext ])
        if self .detected_languages :
            languages_str =', '.join (sorted (self .detected_languages ))
            self .languages_label .setText (f'Языки: {languages_str }')
        else :
            self .languages_label .setText ('Языки: не определены')
    def select_all_files (self ):
        def set_checked (item ,state ):
            path_data =item .data (0 ,Qt .ItemDataRole .UserRole )
            if path_data is not None :
                try :
                    path =Path (path_data )
                    if path .exists ()and path .is_file ():
                        ext =path .suffix .lower ()
                        if ext in self .file_extensions :
                            item .setCheckState (0 ,state )
                except (TypeError ,ValueError ):
                    pass
            for i in range (item .childCount ()):
                set_checked (item .child (i ),state )
        state =Qt .CheckState .Checked
        for i in range (self .file_tree .topLevelItemCount ()):
            set_checked (self .file_tree .topLevelItem (i ),state )
    def deselect_all_files (self ):
        def set_unchecked (item ):
            item .setCheckState (0 ,Qt .CheckState .Unchecked )
            for i in range (item .childCount ()):
                set_unchecked (item .child (i ))
        for i in range (self .file_tree .topLevelItemCount ()):
            set_unchecked (self .file_tree .topLevelItem (i ))
    def process_files (self ):
        selected_files =self .get_selected_files ()
        if not selected_files :
            QMessageBox .warning (self ,'Предупреждение','Выберите файлы для обработки')
            return
        code_files =[f for f in selected_files if f .suffix .lower ()in self .file_extensions ]
        if not code_files :
            QMessageBox .warning (self ,'Предупреждение','Выбранные файлы не являются файлами с кодом. Обрабатываются только файлы с кодом.')
            return
        selected_files =code_files
        if not any ([self .remove_comments_cb .isChecked (),
        self .remove_empty_lines_cb .isChecked (),
        self .remove_trailing_spaces_cb .isChecked (),
        self .normalize_line_endings_cb .isChecked ()]):
            QMessageBox .warning (self ,'Предупреждение','Выберите хотя бы одну опцию очистки')
            return
        reply =QMessageBox .question (
        self ,'Подтверждение',
        f'Обработать {len (selected_files )} файл(ов)?',
        QMessageBox .StandardButton .Yes |QMessageBox .StandardButton .No
        )
        if reply !=QMessageBox .StandardButton .Yes :
            return
        self .progress_bar .setVisible (True )
        self .progress_bar .setMaximum (len (selected_files ))
        self .progress_bar .setValue (0 )
        processed =0
        errors_with_files =[]
        for idx ,file_path in enumerate (selected_files ):
            self .progress_bar .setValue (idx +1 )
            QApplication .processEvents ()
            original_content =None
            try :
                original_content =file_path .read_text (encoding ='utf-8',errors ='ignore')
                if self .backup_files_cb .isChecked ():
                    self .create_backup (file_path )
                content =original_content
                if self .remove_comments_cb .isChecked ():
                    content =self .remove_comments (content ,file_path )
                if self .remove_empty_lines_cb .isChecked ():
                    content =self .remove_empty_lines (content )
                if self .remove_trailing_spaces_cb .isChecked ():
                    content =self .remove_trailing_spaces (content )
                if self .normalize_line_endings_cb .isChecked ():
                    content =self .normalize_line_endings (content )
                error =None
                if self .verify_code_cb .isChecked ():
                    error =self .verify_code (file_path ,content )
                if error :
                    errors_with_files .append ((file_path ,error ,original_content ))
                    self .log (f'⚠ Обнаружена ошибка в {file_path .name }: {error }')
                else :
                    if content !=original_content :
                        self .add_to_history (file_path ,original_content ,'Обработка')
                        file_path .write_text (content ,encoding ='utf-8')
                        processed +=1
                        self .log (f'✓ Обработан: {file_path .name }')
                    else :
                        self .log (f'○ Без изменений: {file_path .name }')
            except Exception as e :
                if original_content is None :
                    try :
                        original_content =file_path .read_text (encoding ='utf-8',errors ='ignore')
                    except :
                        original_content =None
                errors_with_files .append ((file_path ,str (e ),original_content ))
                self .log (f'✗ Ошибка при обработке {file_path .name }: {str (e )}')
        if errors_with_files :
            for file_path ,error_msg ,original_content in errors_with_files :
                if original_content is not None :
                    try :
                        current_content =file_path .read_text (encoding ='utf-8',errors ='ignore')
                        was_modified =current_content !=original_content
                    except :
                        was_modified =False
                    reply =self .show_error_dialog (file_path ,error_msg ,was_modified )
                    if reply =='restore'and was_modified :
                        file_path .write_text (original_content ,encoding ='utf-8')
                        self .log (f'↩ Восстановлен: {file_path .name }')
        if self .create_resources_cb .isChecked ()and 'Python'in self .detected_languages :
            self .create_requirements_file ()
        self .progress_bar .setVisible (False )
        if self .project_path :
            self .update_statistics ()
        msg =f'Обработано файлов: {processed }'
        if errors_with_files :
            msg +=f'\nОшибок: {len (errors_with_files )}'
        else :
            msg +='\nОшибок не обнаружено'
        QMessageBox .information (self ,'Результат',msg )
    def show_error_dialog (self ,file_path :Path ,error_msg :str ,was_modified :bool =False )->str :
        msg_box =QMessageBox (self )
        msg_box .setWindowTitle ('Обнаружена ошибка')
        msg_box .setText (f'В файле {file_path .name } обнаружена ошибка:')
        msg_box .setInformativeText (error_msg )
        msg_box .setIcon (QMessageBox .Icon .Warning )
        restore_btn =msg_box .addButton ('Вернуть',QMessageBox .ButtonRole .ActionRole )
        continue_btn =msg_box .addButton ('Продолжить',QMessageBox .ButtonRole .AcceptRole )
        continue_btn .setStyleSheet ("""
            QPushButton {
                background-color:
                color:
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                min-width: 100px;
            }
            QPushButton: наведите курсор на {
                background-color:
            }
        """)
        restore_btn .setStyleSheet ("""
            QPushButton {
                background-color:
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                min-width: 100px;
            }
            QPushButton: наведите курсор на {
                background-color:
            }
        """)
        msg_box .setDefaultButton (continue_btn )
        if not was_modified :
            restore_btn .setEnabled (False )
            restore_btn .setToolTip ('Файл не был изменен')
        msg_box .exec ()
        clicked_button =msg_box .clickedButton ()
        if clicked_button ==restore_btn :
            return 'restore'
        else :
            return 'continue'
    def remove_comments (self ,content :str ,file_path :Path )->str :
        ext =file_path .suffix .lower ()
        if ext =='.py':
            return self ._remove_python_comments (content )
        elif ext in ['.js','.ts','.jsx','.tsx']:
            return self ._strip_javascript_comments (content )
        elif ext in ['.java','.c','.cpp','.h','.hpp','.ino','.cs','.scala','.kt']:
            lines =content .split ('\n')
            result =[]
            in_multiline =False
            for line in lines :
                if in_multiline :
                    if '*/'in line :
                        in_multiline =False
                        idx =line .find ('*/')
                        remaining =line [idx +2 :]
                        if remaining .strip ():
                            result .append (remaining )
                    continue
                if '/*'in line :
                    start_idx =line .find ('/*')
                    in_string =False
                    string_char =None
                    for i in range (start_idx ):
                        if line [i ]in ['"',"'"]and (i ==0 or line [i -1 ]!='\\'):
                            if not in_string :
                                in_string =True
                                string_char =line [i ]
                            elif line [i ]==string_char :
                                in_string =False
                                string_char =None
                    if not in_string :
                        if '*/'in line [start_idx +2 :]:
                            end_idx =line .find ('*/',start_idx +2 )
                            line =line [:start_idx ]+line [end_idx +2 :]
                        else :
                            in_multiline =True
                            line =line [:start_idx ].rstrip ()
                comment_idx =line .find ('//')
                if comment_idx !=-1 :
                    in_string =False
                    string_char =None
                    for i ,char in enumerate (line [:comment_idx ]):
                        if char in ['"',"'"]and (i ==0 or line [i -1 ]!='\\'):
                            if not in_string :
                                in_string =True
                                string_char =char
                            elif char ==string_char :
                                in_string =False
                                string_char =None
                    if not in_string :
                        line =line [:comment_idx ].rstrip ()
                if line .strip ():
                    result .append (line )
            return '\n'.join (result )
        elif ext =='.html':
            return re .sub (r'<!--.*?-->','',content ,flags =re .DOTALL )
        elif ext =='.css':
            lines =content .split ('\n')
            result =[]
            in_multiline =False
            for line in lines :
                if in_multiline :
                    if '*/'in line :
                        in_multiline =False
                        idx =line .find ('*/')
                        remaining =line [idx +2 :]
                        if remaining .strip ():
                            result .append (remaining )
                    continue
                if '/*'in line :
                    start_idx =line .find ('/*')
                    if '*/'in line [start_idx +2 :]:
                        end_idx =line .find ('*/',start_idx +2 )
                        line =line [:start_idx ]+line [end_idx +2 :]
                    else :
                        in_multiline =True
                        line =line [:start_idx ].rstrip ()
                if line .strip ():
                    result .append (line )
            return '\n'.join (result )
        elif ext =='.sql':
            lines =content .split ('\n')
            result =[]
            in_multiline =False
            for line in lines :
                if in_multiline :
                    if '*/'in line :
                        in_multiline =False
                        idx =line .find ('*/')
                        remaining =line [idx +2 :]
                        if remaining .strip ():
                            result .append (remaining )
                    continue
                if '/*'in line :
                    start_idx =line .find ('/*')
                    in_string =False
                    string_char =None
                    for i in range (start_idx ):
                        if line [i ]in ["'",'"']and (i ==0 or line [i -1 ]!='\\'):
                            if not in_string :
                                in_string =True
                                string_char =line [i ]
                            elif line [i ]==string_char :
                                in_string =False
                                string_char =None
                    if not in_string :
                        if '*/'in line [start_idx +2 :]:
                            end_idx =line .find ('*/',start_idx +2 )
                            line =line [:start_idx ]+line [end_idx +2 :]
                        else :
                            in_multiline =True
                            line =line [:start_idx ].rstrip ()
                comment_idx =line .find ('--')
                if comment_idx !=-1 :
                    in_string =False
                    string_char =None
                    for i ,char in enumerate (line [:comment_idx ]):
                        if char in ["'",'"']and (i ==0 or line [i -1 ]!='\\'):
                            if not in_string :
                                in_string =True
                                string_char =char
                            elif char ==string_char :
                                in_string =False
                                string_char =None
                    if not in_string :
                        line =line [:comment_idx ].rstrip ()
                if line .strip ():
                    result .append (line )
            return '\n'.join (result )
        elif ext =='.php':
            lines =content .split ('\n')
            result =[]
            in_multiline =False
            in_html_comment =False
            for line in lines :
                if in_html_comment :
                    end_idx =line .find ('-->')
                    if end_idx !=-1 :
                        in_html_comment =False
                        remaining =line [end_idx +3 :].strip ()
                        if remaining :
                            line =remaining
                        else :
                            continue
                    else :
                        continue
                if in_multiline :
                    if '*/'in line :
                        in_multiline =False
                        idx =line .find ('*/')
                        remaining =line [idx +2 :]
                        if remaining .strip ():
                            result .append (remaining )
                    continue
                if '/*'in line :
                    start_idx =line .find ('/*')
                    in_string =False
                    string_char =None
                    for i in range (start_idx ):
                        if line [i ]in ['"',"'"]and (i ==0 or line [i -1 ]!='\\'):
                            if not in_string :
                                in_string =True
                                string_char =line [i ]
                            elif line [i ]==string_char :
                                in_string =False
                                string_char =None
                    if not in_string :
                        if '*/'in line [start_idx +2 :]:
                            end_idx =line .find ('*/',start_idx +2 )
                            line =line [:start_idx ]+line [end_idx +2 :]
                        else :
                            in_multiline =True
                            line =line [:start_idx ].rstrip ()
                comment_idx =line .find ('//')
                if comment_idx !=-1 :
                    in_string =False
                    string_char =None
                    for i ,char in enumerate (line [:comment_idx ]):
                        if char in ['"',"'"]and (i ==0 or line [i -1 ]!='\\'):
                            if not in_string :
                                in_string =True
                                string_char =char
                            elif char ==string_char :
                                in_string =False
                                string_char =None
                    if not in_string :
                        line =line [:comment_idx ].rstrip ()
                comment_idx =line .find ('#')
                if comment_idx !=-1 :
                    in_string =False
                    string_char =None
                    for i ,char in enumerate (line [:comment_idx ]):
                        if char in ['"',"'"]and (i ==0 or line [i -1 ]!='\\'):
                            if not in_string :
                                in_string =True
                                string_char =char
                            elif char ==string_char :
                                in_string =False
                                string_char =None
                    if not in_string :
                        line =line [:comment_idx ].rstrip ()
                html_comment_start =line .find ('<!--')
                if html_comment_start !=-1 :
                    html_comment_end =line .find ('-->',html_comment_start +4 )
                    if html_comment_end !=-1 :
                        line =(line [:html_comment_start ]+line [html_comment_end +3 :]).strip ()
                    else :
                        line =line [:html_comment_start ].rstrip ()
                        in_html_comment =True
                if line .strip ():
                    result .append (line )
            return '\n'.join (result )
        elif ext in ['.rb']:
            lines =content .split ('\n')
            result =[]
            for line in lines :
                comment_idx =line .find ('#')
                if comment_idx !=-1 :
                    in_string =False
                    string_char =None
                    for i ,char in enumerate (line [:comment_idx ]):
                        if char in ['"',"'"]and (i ==0 or line [i -1 ]!='\\'):
                            if not in_string :
                                in_string =True
                                string_char =char
                            elif char ==string_char :
                                in_string =False
                                string_char =None
                    if not in_string :
                        line =line [:comment_idx ].rstrip ()
                if line .strip ():
                    result .append (line )
            return '\n'.join (result )
        elif ext in ['.go']:
            lines =content .split ('\n')
            result =[]
            in_multiline =False
            for line in lines :
                if in_multiline :
                    if '*/'in line :
                        in_multiline =False
                        idx =line .find ('*/')
                        remaining =line [idx +2 :]
                        if remaining .strip ():
                            result .append (remaining )
                    continue
                if '/*'in line :
                    start_idx =line .find ('/*')
                    in_string =False
                    string_char =None
                    for i in range (start_idx ):
                        if line [i ]in ['"','`',"'"]and (i ==0 or line [i -1 ]!='\\'):
                            if not in_string :
                                in_string =True
                                string_char =line [i ]
                            elif line [i ]==string_char :
                                in_string =False
                                string_char =None
                    if not in_string :
                        if '*/'in line [start_idx +2 :]:
                            end_idx =line .find ('*/',start_idx +2 )
                            line =line [:start_idx ]+line [end_idx +2 :]
                        else :
                            in_multiline =True
                            line =line [:start_idx ].rstrip ()
                comment_idx =line .find ('//')
                if comment_idx !=-1 :
                    in_string =False
                    for i ,char in enumerate (line [:comment_idx ]):
                        if char in ['"','`',"'"]and (i ==0 or line [i -1 ]!='\\'):
                            in_string =not in_string
                    if not in_string :
                        line =line [:comment_idx ].rstrip ()
                if line .strip ():
                    result .append (line )
            return '\n'.join (result )
        elif ext in ['.rs']:
            lines =content .split ('\n')
            result =[]
            in_multiline =False
            for line in lines :
                if in_multiline :
                    if '*/'in line :
                        in_multiline =False
                        idx =line .find ('*/')
                        remaining =line [idx +2 :]
                        if remaining .strip ():
                            result .append (remaining )
                    continue
                if '/*'in line :
                    start_idx =line .find ('/*')
                    in_string =False
                    string_char =None
                    for i in range (start_idx ):
                        if line [i ]in ['"',"'"]and (i ==0 or line [i -1 ]!='\\'):
                            if not in_string :
                                in_string =True
                                string_char =line [i ]
                            elif line [i ]==string_char :
                                in_string =False
                                string_char =None
                    if not in_string :
                        if '*/'in line [start_idx +2 :]:
                            end_idx =line .find ('*/',start_idx +2 )
                            line =line [:start_idx ]+line [end_idx +2 :]
                        else :
                            in_multiline =True
                            line =line [:start_idx ].rstrip ()
                comment_idx =line .find ('//')
                if comment_idx !=-1 :
                    in_string =False
                    for i ,char in enumerate (line [:comment_idx ]):
                        if char in ['"',"'"]and (i ==0 or line [i -1 ]!='\\'):
                            in_string =not in_string
                    if not in_string :
                        line =line [:comment_idx ].rstrip ()
                if line .strip ():
                    result .append (line )
            return '\n'.join (result )
        elif ext in ['.swift']:
            lines =content .split ('\n')
            result =[]
            in_multiline =False
            for line in lines :
                if in_multiline :
                    if '*/'in line :
                        in_multiline =False
                        idx =line .find ('*/')
                        remaining =line [idx +2 :]
                        if remaining .strip ():
                            result .append (remaining )
                    continue
                if '/*'in line :
                    start_idx =line .find ('/*')
                    in_string =False
                    string_char =None
                    for i in range (start_idx ):
                        if line [i ]in ['"',"'"]and (i ==0 or line [i -1 ]!='\\'):
                            if not in_string :
                                in_string =True
                                string_char =line [i ]
                            elif line [i ]==string_char :
                                in_string =False
                                string_char =None
                    if not in_string :
                        if '*/'in line [start_idx +2 :]:
                            end_idx =line .find ('*/',start_idx +2 )
                            line =line [:start_idx ]+line [end_idx +2 :]
                        else :
                            in_multiline =True
                            line =line [:start_idx ].rstrip ()
                comment_idx =line .find ('//')
                if comment_idx !=-1 :
                    in_string =False
                    for i ,char in enumerate (line [:comment_idx ]):
                        if char in ['"',"'"]and (i ==0 or line [i -1 ]!='\\'):
                            in_string =not in_string
                    if not in_string :
                        line =line [:comment_idx ].rstrip ()
                if line .strip ():
                    result .append (line )
            return '\n'.join (result )
        elif ext in ['.r']:
            lines =content .split ('\n')
            result =[]
            for line in lines :
                comment_idx =line .find ('#')
                if comment_idx !=-1 :
                    in_string =False
                    string_char =None
                    for i ,char in enumerate (line [:comment_idx ]):
                        if char in ['"',"'"]and (i ==0 or line [i -1 ]!='\\'):
                            if not in_string :
                                in_string =True
                                string_char =char
                            elif char ==string_char :
                                in_string =False
                                string_char =None
                    if not in_string :
                        line =line [:comment_idx ].rstrip ()
                if line .strip ():
                    result .append (line )
            return '\n'.join (result )
        elif ext in ['.m']:
            lines =content .split ('\n')
            result =[]
            in_multiline =False
            for line in lines :
                if in_multiline :
                    if '*/'in line :
                        in_multiline =False
                        idx =line .find ('*/')
                        remaining =line [idx +2 :]
                        if remaining .strip ():
                            result .append (remaining )
                    continue
                if '/*'in line :
                    start_idx =line .find ('/*')
                    in_string =False
                    string_char =None
                    for i in range (start_idx ):
                        if line [i ]in ['"',"'"]and (i ==0 or line [i -1 ]!='\\'):
                            if not in_string :
                                in_string =True
                                string_char =line [i ]
                            elif line [i ]==string_char :
                                in_string =False
                                string_char =None
                    if not in_string :
                        if '*/'in line [start_idx +2 :]:
                            end_idx =line .find ('*/',start_idx +2 )
                            line =line [:start_idx ]+line [end_idx +2 :]
                        else :
                            in_multiline =True
                            line =line [:start_idx ].rstrip ()
                comment_idx =line .find ('//')
                if comment_idx !=-1 :
                    in_string =False
                    for i ,char in enumerate (line [:comment_idx ]):
                        if char in ['"',"'"]and (i ==0 or line [i -1 ]!='\\'):
                            in_string =not in_string
                    if not in_string :
                        line =line [:comment_idx ].rstrip ()
                if line .strip ():
                    result .append (line )
            return '\n'.join (result )
        elif ext in ['.scss']:
            lines =content .split ('\n')
            result =[]
            in_multiline =False
            for line in lines :
                if in_multiline :
                    if '*/'in line :
                        in_multiline =False
                        idx =line .find ('*/')
                        remaining =line [idx +2 :]
                        if remaining .strip ():
                            result .append (remaining )
                    continue
                if '/*'in line :
                    start_idx =line .find ('/*')
                    if '*/'in line [start_idx +2 :]:
                        end_idx =line .find ('*/',start_idx +2 )
                        line =line [:start_idx ]+line [end_idx +2 :]
                    else :
                        in_multiline =True
                        line =line [:start_idx ].rstrip ()
                comment_idx =line .find ('//')
                if comment_idx !=-1 :
                    line =line [:comment_idx ].rstrip ()
                if line .strip ():
                    result .append (line )
            return '\n'.join (result )
        elif ext in ['.vue']:
            content =re .sub (r'<!--.*?-->','',content ,flags =re .DOTALL )
            lines =content .split ('\n')
            result =[]
            in_script =False
            in_multiline =False
            for line in lines :
                if '<скрипт'in line .lower ():
                    in_script =True
                if '</скрипт>'in line .lower ():
                    in_script =False
                if in_script :
                    if in_multiline :
                        if '*/'in line :
                            in_multiline =False
                            idx =line .find ('*/')
                            remaining =line [idx +2 :]
                            if remaining .strip ():
                                result .append (remaining )
                        continue
                    if '/*'in line :
                        start_idx =line .find ('/*')
                        if '*/'in line [start_idx +2 :]:
                            end_idx =line .find ('*/',start_idx +2 )
                            line =line [:start_idx ]+line [end_idx +2 :]
                        else :
                            in_multiline =True
                            line =line [:start_idx ].rstrip ()
                    comment_idx =line .find ('//')
                    if comment_idx !=-1 :
                        in_string =False
                        for i ,char in enumerate (line [:comment_idx ]):
                            if char in ['"',"'"]and (i ==0 or line [i -1 ]!='\\'):
                                in_string =not in_string
                        if not in_string :
                            line =line [:comment_idx ].rstrip ()
                result .append (line )
            return '\n'.join (result )
        elif ext in ['.xml']:
            return re .sub (r'<!--.*?-->','',content ,flags =re .DOTALL )
        elif ext in ['.yaml','.yml']:
            lines =content .split ('\n')
            result =[]
            for line in lines :
                comment_idx =line .find ('#')
                if comment_idx !=-1 :
                    before_comment =line [:comment_idx ].strip ()
                    if not before_comment or before_comment .endswith (':')or before_comment .endswith ('-'):
                        in_string =False
                        string_char =None
                        for i ,char in enumerate (line [:comment_idx ]):
                            if char in ['"',"'"]and (i ==0 or line [i -1 ]!='\\'):
                                if not in_string :
                                    in_string =True
                                    string_char =char
                                elif char ==string_char :
                                    in_string =False
                                    string_char =None
                        if not in_string :
                            line =line [:comment_idx ].rstrip ()
                if line .strip ():
                    result .append (line )
            return '\n'.join (result )
        elif ext in ['.sh']:
            lines =content .split ('\n')
            result =[]
            for line in lines :
                comment_idx =line .find ('#')
                if comment_idx !=-1 :
                    if comment_idx ==0 and line .startswith ('#!'):
                        result .append (line )
                        continue
                    in_string =False
                    string_char =None
                    for i ,char in enumerate (line [:comment_idx ]):
                        if char in ['"',"'"]and (i ==0 or line [i -1 ]!='\\'):
                            if not in_string :
                                in_string =True
                                string_char =char
                            elif char ==string_char :
                                in_string =False
                                string_char =None
                    if not in_string :
                        line =line [:comment_idx ].rstrip ()
                if line .strip ():
                    result .append (line )
            return '\n'.join (result )
        elif ext in ['.bat']:
            lines =content .split ('\n')
            result =[]
            for line in lines :
                stripped =line .strip ()
                if stripped .upper ().startswith ('REM '):
                    continue
                if stripped .startswith ('::'):
                    continue
                if stripped .upper ().startswith ('REM'):
                    if len (stripped )==3 or (len (stripped )>3 and stripped [3 ]in [' ','\t']):
                        continue
                result .append (line )
            return '\n'.join (result )
        elif ext in ['.ps1']:
            lines =content .split ('\n')
            result =[]
            for line in lines :
                comment_idx =line .find ('#')
                if comment_idx !=-1 :
                    in_string =False
                    string_char =None
                    for i ,char in enumerate (line [:comment_idx ]):
                        if char in ['"',"'"]and (i ==0 or line [i -1 ]!='\\'):
                            if not in_string :
                                in_string =True
                                string_char =char
                            elif char ==string_char :
                                in_string =False
                                string_char =None
                    if not in_string :
                        line =line [:comment_idx ].rstrip ()
                if line .strip ():
                    result .append (line )
            return '\n'.join (result )
        return content
    def _remove_python_comments (self ,content :str )->str :
        try :
            tokens =tokenize .generate_tokens (io .StringIO (content ).readline )
            cleaned_tokens =[tok for tok in tokens if tok .type !=tokenize .COMMENT ]
            return tokenize .untokenize (cleaned_tokens )
        except (tokenize .TokenError ,IndentationError ,SyntaxError ):
            return content
    def _is_js_identifier_start (self ,char :str )->bool :
        return char =='_'or char =='$'or char .isalpha ()
    def _is_js_identifier_part (self ,char :str )->bool :
        return self ._is_js_identifier_start (char )or char .isdigit ()
    def _can_start_js_regex (self ,previous_token :str )->bool :
        return previous_token in {
        None ,
        'operator',
        'comma',
        'colon',
        'question',
        'semicolon',
        'open_paren',
        'open_brace',
        'open_bracket',
        'keyword_prefix'
        }
    def _scan_javascript (self ,content :str ,strip_comments :bool =False )->Tuple [str ,int ,int ,int ,str ]:
        result =[]
        brace_balance =0
        paren_balance =0
        bracket_balance =0
        brace_stack =[]
        previous_token =None
        mode ='code'
        quote_char =None
        regex_in_class =False
        block_comment_has_newline =False
        i =0
        length =len (content )
        regex_prefix_keywords ={
        'await','case','delete','do','else','in','instanceof',
        'new','of','return','throw','typeof','void','yield'
        }
        while i <length :
            char =content [i ]
            next_char =content [i +1 ]if i +1 <length else ''
            if mode =='line_comment':
                if char =='\n':
                    if strip_comments :
                        result .append ('\n')
                    mode ='code'
                i +=1
                continue
            if mode =='block_comment':
                if char =='\n':
                    block_comment_has_newline =True
                    if strip_comments :
                        result .append ('\n')
                    i +=1
                    continue
                if char =='*'and next_char =='/':
                    if strip_comments and not block_comment_has_newline :
                        upcoming =content [i +2 ]if i +2 <length else ''
                        if result and not result [-1 ].isspace ()and upcoming and not upcoming .isspace ():
                            result .append (' ')
                    mode ='code'
                    i +=2
                    continue
                i +=1
                continue
            if mode =='string':
                if strip_comments :
                    result .append (char )
                if char =='\\':
                    if i +1 <length :
                        if strip_comments :
                            result .append (content [i +1 ])
                        i +=2
                        continue
                elif char ==quote_char :
                    mode ='code'
                    previous_token ='string'
                i +=1
                continue
            if mode =='template':
                if strip_comments :
                    result .append (char )
                if char =='\\':
                    if i +1 <length :
                        if strip_comments :
                            result .append (content [i +1 ])
                        i +=2
                        continue
                elif char =='`':
                    mode ='code'
                    previous_token ='string'
                    i +=1
                    continue
                elif char =='$'and next_char =='{':
                    brace_balance +=1
                    brace_stack .append (True )
                    previous_token ='open_brace'
                    if strip_comments :
                        result .append (next_char )
                    mode ='code'
                    i +=2
                    continue
                i +=1
                continue
            if mode =='regex':
                if strip_comments :
                    result .append (char )
                if char =='\\':
                    if i +1 <length :
                        if strip_comments :
                            result .append (content [i +1 ])
                        i +=2
                        continue
                elif char =='[':
                    regex_in_class =True
                elif char ==']'and regex_in_class :
                    regex_in_class =False
                elif char =='/'and not regex_in_class :
                    i +=1
                    while i <length and content [i ].isalpha ():
                        if strip_comments :
                            result .append (content [i ])
                        i +=1
                    previous_token ='regex'
                    mode ='code'
                    continue
                i +=1
                continue
            if char .isspace ():
                if strip_comments :
                    result .append (char )
                i +=1
                continue
            if char =='/'and next_char =='/':
                mode ='line_comment'
                i +=2
                continue
            if char =='/'and next_char =='*':
                mode ='block_comment'
                block_comment_has_newline =False
                i +=2
                continue
            if char in ["'",'"']:
                if strip_comments :
                    result .append (char )
                quote_char =char
                mode ='string'
                i +=1
                continue
            if char =='`':
                if strip_comments :
                    result .append (char )
                mode ='template'
                i +=1
                continue
            if char =='/'and self ._can_start_js_regex (previous_token ):
                if strip_comments :
                    result .append (char )
                mode ='regex'
                regex_in_class =False
                i +=1
                continue
            if self ._is_js_identifier_start (char ):
                start =i
                i +=1
                while i <length and self ._is_js_identifier_part (content [i ]):
                    i +=1
                word =content [start :i ]
                if strip_comments :
                    result .append (word )
                if word in regex_prefix_keywords :
                    previous_token ='keyword_prefix'
                else :
                    previous_token ='identifier'
                continue
            if char .isdigit ():
                start =i
                i +=1
                while i <length and (content [i ].isalnum ()or content [i ]in '._'):
                    i +=1
                if strip_comments :
                    result .append (content [start :i ])
                previous_token ='number'
                continue
            if char =='{':
                brace_balance +=1
                brace_stack .append (False )
                previous_token ='open_brace'
            elif char =='}':
                brace_balance -=1
                previous_token ='close_brace'
                template_expr =brace_stack .pop ()if brace_stack else False
                if strip_comments :
                    result .append (char )
                i +=1
                if template_expr :
                    mode ='template'
                continue
            elif char =='(':
                paren_balance +=1
                previous_token ='open_paren'
            elif char ==')':
                paren_balance -=1
                previous_token ='close_paren'
            elif char =='[':
                bracket_balance +=1
                previous_token ='open_bracket'
            elif char ==']':
                bracket_balance -=1
                previous_token ='close_bracket'
            elif char ==',':
                previous_token ='comma'
            elif char ==':':
                previous_token ='colon'
            elif char =='?':
                previous_token ='question'
            elif char ==';':
                previous_token ='semicolon'
            else :
                previous_token ='operator'
            if strip_comments :
                result .append (char )
            i +=1
        if mode =='string':
            state_error ='Незакрытая строка'
        elif mode =='template':
            state_error ='Незакрытый шаблонный литерал'
        elif mode =='regex':
            state_error ='Незакрытое регулярное выражение'
        elif mode =='block_comment':
            state_error ='Незакрытый блок комментария'
        else :
            state_error =None
        cleaned_content =''.join (result )if strip_comments else content
        return cleaned_content ,brace_balance ,paren_balance ,bracket_balance ,state_error
    def _strip_javascript_comments (self ,content :str )->str :
        cleaned_content ,_brace_balance ,_paren_balance ,_bracket_balance ,_state_error =self ._scan_javascript (content ,strip_comments =True )
        return cleaned_content
    def _is_qt_translation_file (self ,file_path :Path ,content :str )->bool :
        if file_path .suffix .lower ()!='.ts':
            return False
        header =content .lstrip ('\ufeff')[:512 ].lower ()
        return ('<?xml'in header and '<!doctype ts'in header )or '<ts version='in header or header .startswith ('<ts ')
    def _strip_qml_pragma_lines (self ,content :str )->str :
        if '.pragma'not in content :
            return content
        result =[]
        changed =False
        for line in content .splitlines (keepends =True ):
            if line .lstrip ().startswith ('.pragma '):
                result .append ('\n'if line .endswith ('\n')else '')
                changed =True
            else :
                result .append (line )
        return ''.join (result )if changed else content
    def _get_javascript_tree_sitter_parser (self ):
        global _TREE_SITTER_JS_LANGUAGE ,_TREE_SITTER_JS_PARSER ,_TREE_SITTER_JS_INIT_ATTEMPTED
        if _TREE_SITTER_JS_INIT_ATTEMPTED :
            return _TREE_SITTER_JS_PARSER
        _TREE_SITTER_JS_INIT_ATTEMPTED =True
        try :
            from tree_sitter import Language ,Parser
            import tree_sitter_javascript as tree_sitter_javascript
        except Exception :
            if _TREE_SITTER_JS_PATH .exists ():
                tree_sitter_path_str =str (_TREE_SITTER_JS_PATH )
                if tree_sitter_path_str not in sys .path :
                    sys .path .insert (0 ,tree_sitter_path_str )
            try :
                from tree_sitter import Language ,Parser
                import tree_sitter_javascript as tree_sitter_javascript
            except Exception :
                return None
        try :
            _TREE_SITTER_JS_LANGUAGE =Language (tree_sitter_javascript .language ())
            _TREE_SITTER_JS_PARSER =Parser (_TREE_SITTER_JS_LANGUAGE )
        except Exception :
            _TREE_SITTER_JS_LANGUAGE =None
            _TREE_SITTER_JS_PARSER =None
        return _TREE_SITTER_JS_PARSER
    def _get_typescript_tree_sitter_parser (self ,ext :str ):
        global _TREE_SITTER_TS_LANGUAGE ,_TREE_SITTER_TSX_LANGUAGE ,_TREE_SITTER_TS_PARSER ,_TREE_SITTER_TSX_PARSER ,_TREE_SITTER_TS_INIT_ATTEMPTED
        if not _TREE_SITTER_TS_INIT_ATTEMPTED :
            _TREE_SITTER_TS_INIT_ATTEMPTED =True
            try :
                from tree_sitter import Language ,Parser
                import tree_sitter_typescript as tree_sitter_typescript
            except Exception :
                if _TREE_SITTER_JS_PATH .exists ():
                    tree_sitter_path_str =str (_TREE_SITTER_JS_PATH )
                    if tree_sitter_path_str not in sys .path :
                        sys .path .insert (0 ,tree_sitter_path_str )
                try :
                    from tree_sitter import Language ,Parser
                    import tree_sitter_typescript as tree_sitter_typescript
                except Exception :
                    return None
            try :
                _TREE_SITTER_TS_LANGUAGE =Language (tree_sitter_typescript .language_typescript ())
                _TREE_SITTER_TSX_LANGUAGE =Language (tree_sitter_typescript .language_tsx ())
                _TREE_SITTER_TS_PARSER =Parser (_TREE_SITTER_TS_LANGUAGE )
                _TREE_SITTER_TSX_PARSER =Parser (_TREE_SITTER_TSX_LANGUAGE )
            except Exception :
                _TREE_SITTER_TS_LANGUAGE =None
                _TREE_SITTER_TSX_LANGUAGE =None
                _TREE_SITTER_TS_PARSER =None
                _TREE_SITTER_TSX_PARSER =None
        if ext =='.tsx':
            return _TREE_SITTER_TSX_PARSER
        return _TREE_SITTER_TS_PARSER
    def _find_tree_sitter_error_node (self ,node ):
        if node is None :
            return None
        if node .type =='ERROR'or node .is_missing :
            return node
        for child in node .children :
            error_node =self ._find_tree_sitter_error_node (child )
            if error_node is not None :
                return error_node
        return None
    def _verify_javascript_with_tree_sitter (self ,content :str ,ext :str ):
        if ext not in ['.js','.jsx']:
            return None
        parser =self ._get_javascript_tree_sitter_parser ()
        if parser is None :
            return None
        try :
            tree =parser .parse (content .encode ('utf-8',errors ='ignore'))
            error_node =self ._find_tree_sitter_error_node (tree .root_node )
            if error_node is None and not tree .root_node .has_error :
                return ''
            if error_node is None :
                row ,column =(0 ,0 )
            else :
                row ,column =error_node .start_point
            return f'Синтаксическая ошибка: JS/JSX parse error near line {row +1 }, column {column +1 }'
        except Exception :
            return None
    def _verify_typescript_with_tree_sitter (self ,content :str ,ext :str ):
        if ext not in ['.ts','.tsx']:
            return None
        parser =self ._get_typescript_tree_sitter_parser (ext )
        if parser is None :
            return None
        try :
            tree =parser .parse (content .encode ('utf-8',errors ='ignore'))
            error_node =self ._find_tree_sitter_error_node (tree .root_node )
            if error_node is None and not tree .root_node .has_error :
                return ''
            if error_node is None :
                row ,column =(0 ,0 )
            else :
                row ,column =error_node .start_point
            return f'Синтаксическая ошибка: TS/TSX parse error near line {row +1 }, column {column +1 }'
        except Exception :
            return None
    def remove_empty_lines (self ,content :str )->str :
        lines =content .split ('\n')
        result =[]
        prev_empty =False
        for line in lines :
            if line .strip ():
                result .append (line )
                prev_empty =False
            elif not prev_empty :
                result .append ('')
                prev_empty =True
        while result and not result [0 ].strip ():
            result .pop (0 )
        while result and not result [-1 ].strip ():
            result .pop ()
        return '\n'.join (result )
    def remove_trailing_spaces (self ,content :str )->str :
        lines =content .split ('\n')
        return '\n'.join (line .rstrip ()for line in lines )
    def normalize_line_endings (self ,content :str )->str :
        content =content .replace ('\r\n','\n').replace ('\r','\n')
        return content
    def verify_code (self ,file_path :Path ,content :str )->str :
        ext =file_path .suffix .lower ()
        if ext =='.py':
            try :
                compile (content ,str (file_path ),'exec')
            except SyntaxError as e :
                return f'Синтаксическая ошибка: {e .msg } на строке {e .lineno }'
            except Exception as e :
                return f'Ошибка компиляции: {str (e )}'
        elif ext in ['.js','.jsx','.ts','.tsx']:
            if self ._is_qt_translation_file (file_path ,content ):
                return None
            verification_content =self ._strip_qml_pragma_lines (content )
            if ext in ['.ts','.tsx']:
                tree_sitter_result =self ._verify_typescript_with_tree_sitter (verification_content ,ext )
            else :
                tree_sitter_result =self ._verify_javascript_with_tree_sitter (verification_content ,ext )
            if tree_sitter_result =='':
                return None
            if tree_sitter_result is not None :
                return tree_sitter_result
            _cleaned_content ,open_braces ,open_parens ,open_brackets ,state_error =self ._scan_javascript (verification_content )
            if ext in ['.jsx','.tsx']:
                if state_error :
                    return f'Синтаксическая ошибка: {state_error }'
                return None
            if ext in ['.ts','.tsx']:
                if state_error :
                    return f'Синтаксическая ошибка: {state_error }'
                return None
            errors =[]
            if state_error :
                errors .append (f'Синтаксическая ошибка: {state_error }')
            if open_braces !=0 :
                errors .append (f'Несоответствие фигурных скобок: {open_braces }')
            if open_parens !=0 :
                errors .append (f'Несоответствие круглых скобок: {open_parens }')
            if open_brackets !=0 :
                errors .append (f'Несоответствие квадратных скобок: {open_brackets }')
            if errors :
                return '; '.join (errors )
        return None
    def create_backup (self ,file_path :Path ):
        backup_path =file_path .with_suffix (file_path .suffix +'.backup')
        try :
            backup_path .write_bytes (file_path .read_bytes ())
        except Exception :
            pass
    def create_requirements_file (self ):
        if not self .project_path :
            return
        dependencies =set ()
        stdlib_modules ={
        'sys','os','re','pathlib','typing','collections','datetime',
        'json','xml','urllib','http','email','sqlite3','csv',
        'logging','unittest','threading','multiprocessing','asyncio',
        'itertools','functools','operator','copy','pickle','hashlib',
        'base64','random','math','statistics','decimal','fractions',
        'string','textwrap','unicodedata','locale','gettext','argparse',
        'configparser','shutil','tempfile','glob','fnmatch','linecache',
        'codecs','io','gzip','bz2','lzma','zipfile','tarfile',
        'struct','array','ctypes','mmap','select','selectors',
        'socket','ssl','socketserver','queue','sched','time','calendar',
        'locale','gettext','argparse','getopt','logging','warnings',
        'dataclasses','enum','types','weakref','gc','inspect','ast',
        'dis','pdb','profile','pstats','timeit','trace','tracemalloc',
        'faulthandler','pydoc','doctest','unittest','test','lib2to3',
        'distutils','ensurepip','venv','zipapp','compileall','py_compile',
        'keyword','token','tokenize','tabnanny','pyclbr','py_compile',
        'compileall','dis','pickletools','formatter','msilib','msvcrt',
        'winreg','winsound','posix','pwd','spwd','grp','crypt',
        'termios','tty','pty','fcntl','pipes','resource','nis',
        'syslog','platform','errno','signal','subprocess','sched',
        'queue','select','selectors','asyncio','concurrent','multiprocessing',
        'threading','_thread','dummy_threading','queue','contextvars',
        'traceback','builtins','__builtin__','future_builtins','copyreg',
        'gc','inspect','site','fpectl','atexit','abc','collections',
        'collections.abc','heapq','bisect','array','weakref','types',
        'copy','pprint','reprlib','enum','numbers','math','cmath',
        'decimal','fractions','statistics','random','secrets','statistics',
        'string','re','difflib','textwrap','unicodedata','stringprep',
        'readline','rlcompleter','struct','codecs','encodings','io',
        'fileinput','stat','filecmp','tempfile','glob','fnmatch',
        'linecache','shutil','pickle','copyreg','shelve','marshal',
        'dbm','sqlite3','zlib','gzip','bz2','lzma','zipfile','tarfile',
        'csv','configparser','netrc','xdrlib','plistlib','hashlib',
        'hmac','secrets','os','io','argparse','getopt','logging',
        'logging.config','logging.handlers','getpass','curses','platform',
        'errno','ctypes','ctypes.util','ctypes.wintypes','msilib',
        'msvcrt','winreg','winsound','posix','pwd','spwd','grp',
        'crypt','termios','tty','pty','fcntl','pipes','resource',
        'nis','syslog','sys','sysconfig','builtins','__builtin__',
        'future_builtins','warnings','contextlib','abc','atexit',
        'traceback','gc','inspect','site','fpectl','user','bdb',
        'pdb','profile','pstats','timeit','trace','tracemalloc',
        'faulthandler','pydoc','doctest','unittest','unittest.mock',
        'test','test.support','lib2to3','distutils','ensurepip','venv',
        'zipapp','compileall','py_compile','keyword','token','tokenize',
        'tabnanny','pyclbr','py_compile','compileall','dis','pickletools',
        'formatter','msilib','msvcrt','winreg','winsound','posix',
        'pwd','spwd','grp','crypt','termios','tty','pty','fcntl',
        'pipes','resource','nis','syslog','platform','errno','signal',
        'subprocess','sched','queue','select','selectors','asyncio',
        'concurrent','multiprocessing','threading','_thread','dummy_threading',
        'queue','contextvars','traceback','builtins','__builtin__',
        'future_builtins','copyreg','gc','inspect','site','fpectl',
        'atexit','abc','collections','collections.abc','heapq','bisect',
        'array','weakref','types','copy','pprint','reprlib','enum',
        'numbers','math','cmath','decimal','fractions','statistics',
        'random','secrets','statistics','string','re','difflib',
        'textwrap','unicodedata','stringprep','readline','rlcompleter',
        'struct','codecs','encodings','io','fileinput','stat','filecmp',
        'tempfile','glob','fnmatch','linecache','shutil','pickle',
        'copyreg','shelve','marshal','dbm','sqlite3','zlib','gzip',
        'bz2','lzma','zipfile','tarfile','csv','configparser','netrc',
        'xdrlib','plistlib','hashlib','hmac','secrets','os','io',
        'argparse','getopt','logging','logging.config','logging.handlers',
        'getpass','curses','platform','errno','ctypes','ctypes.util',
        'ctypes.wintypes','msilib','msvcrt','winreg','winsound','posix',
        'pwd','spwd','grp','crypt','termios','tty','pty','fcntl',
        'pipes','resource','nis','syslog','sys','sysconfig','builtins',
        '__builtin__','future_builtins','warnings','contextlib','abc',
        'atexit','traceback','gc','inspect','site','fpectl','user',
        'bdb','pdb','profile','pstats','timeit','trace','tracemalloc',
        'faulthandler','pydoc','doctest','unittest','unittest.mock','test',
        'test.support','lib2to3','distutils','ensurepip','venv','zipapp',
        'compileall','py_compile','keyword','token','tokenize','tabnanny',
        'pyclbr','py_compile','compileall','dis','pickletools','formatter'
        }
        for py_file in self .project_path .rglob ('*.py'):
            if '__pycache__'in str (py_file )or '.pyc'in str (py_file ):
                continue
            try :
                content =py_file .read_text (encoding ='utf-8',errors ='ignore')
                import_pattern =re .compile (r'^(?:from\s+(\S+)\s+)?import\s+(\S+)',re .MULTILINE )
                matches =import_pattern .findall (content )
                for from_module ,import_module in matches :
                    if from_module :
                        module =from_module .split ('.')[0 ]
                    else :
                        module =import_module .split ('.')[0 ].split (' as ')[0 ]
                    if module and not module .startswith ('.')and module not in stdlib_modules :
                        dependencies .add (module )
            except Exception :
                continue
        if not dependencies and 'Python'in self .detected_languages :
            for py_file in self .project_path .rglob ('*.py'):
                if '__pycache__'in str (py_file ):
                    continue
                try :
                    content =py_file .read_text (encoding ='utf-8',errors ='ignore')
                    if 'PyQt6'in content or 'from PyQt6'in content or 'import PyQt6'in content :
                        dependencies .add ('PyQt6')
                        break
                except Exception :
                    continue
        if not dependencies and 'Python'in self .detected_languages :
            dependencies .add ('PyQt6')
        dependencies_list =sorted (dependencies )
        requirements_file =self .project_path /'requirements.txt'
        if dependencies_list :
            requirements_file .write_text ('\n'.join (dependencies_list ),encoding ='utf-8')
            self .log (f'✓ Создан файл requirements.txt с зависимостями: {", ".join (dependencies_list )}')
        else :
            self .log ('⚠ Не найдено зависимостей для requirements.txt')
    def delete_selected_files (self ):
        selected_files =self .get_selected_files ()
        if not selected_files :
            QMessageBox .warning (self ,'Предупреждение','Выберите файлы для удаления')
            return
        reply =QMessageBox .question (
        self ,'Подтверждение удаления',
        f'Удалить {len (selected_files )} файл(ов)?\n\nЭто действие нельзя отменить!',
        QMessageBox .StandardButton .Yes |QMessageBox .StandardButton .No ,
        QMessageBox .StandardButton .No
        )
        if reply !=QMessageBox .StandardButton .Yes :
            return
        deleted =0
        errors =[]
        for file_path in selected_files :
            try :
                file_path .unlink ()
                deleted +=1
                self .log (f'🗑️ Удален: {file_path .name }')
            except Exception as e :
                errors .append (f'{file_path .name }: {str (e )}')
        self .load_project_files ()
        msg =f'Удалено файлов: {deleted }'
        if errors :
            msg +=f'\nОшибок: {len (errors )}'
        QMessageBox .information (self ,'Результат',msg )
    def update_statistics (self ):
        if not self .project_path :
            self .stats_table .setRowCount (0 )
            return
        stats =self .calculate_statistics ()
        if not stats :
            self .stats_table .setRowCount (0 )
            return
        self .stats_table .setRowCount (len (stats ))
        for row ,(key ,value )in enumerate (stats .items ()):
            self .stats_table .setItem (row ,0 ,QTableWidgetItem (str (key )))
            self .stats_table .setItem (row ,1 ,QTableWidgetItem (str (value )))
        self .stats_table .resizeColumnsToContents ()
    def calculate_statistics (self )->dict :
        if not self .project_path :
            return {}
        total_files =0
        total_lines =0
        total_lines_no_comments =0
        total_comments =0
        total_functions =0
        total_classes =0
        total_size =0
        files_by_language ={}
        for file_path in self .project_path .rglob ('*'):
            if file_path .is_file ()and '__pycache__'not in str (file_path ):
                try :
                    size =file_path .stat ().st_size
                    total_size +=size
                    ext =file_path .suffix .lower ()
                    if ext in self .file_extensions :
                        lang =self .file_extensions [ext ]
                        files_by_language [lang ]=files_by_language .get (lang ,0 )+1
                        total_files +=1
                        content =file_path .read_text (encoding ='utf-8',errors ='ignore')
                        lines =content .split ('\n')
                        total_lines +=len (lines )
                        for line in lines :
                            stripped =line .strip ()
                            if stripped .startswith ('#'):
                                total_comments +=1
                            elif ext =='.py':
                                if stripped .startswith ('def ')or stripped .startswith ('асинхронная защита '):
                                    total_functions +=1
                                elif stripped .startswith ('class '):
                                    total_classes +=1
                        cleaned =self .remove_comments (content ,file_path )
                        total_lines_no_comments +=len (cleaned .split ('\n'))
                except Exception :
                    continue
        comment_percentage =(total_comments /total_lines *100 )if total_lines >0 else 0
        stats ={
        'Всего файлов':total_files ,
        'Всего строк кода':total_lines ,
        'Строк без комментариев':total_lines_no_comments ,
        'Строк комментариев':total_comments ,
        'Процент комментариев':f'{comment_percentage :.2f}%',
        'Функций (Python)':total_functions ,
        'Классов (Python)':total_classes ,
        'Общий размер':f'{total_size /1024 :.2f} KB',
        'Файлов по языкам':', '.join ([f'{k }: {v }'for k ,v in files_by_language .items ()])
        }
        return stats
    def open_folder (self ):
        folder =QFileDialog .getExistingDirectory (self ,'Выберите папку проекта')
        if folder :
            self .project_path =Path (folder )
            self .invalidate_project_cache ()
            self .project_label .setText (f'Проект: {self .project_path .name }')
            self .load_project_files ()
            self .detect_languages ()
            self .update_statistics ()
            self .log (f'Открыт проект: {self .project_path }')
    def invalidate_project_cache (self ):
        self .project_index_ready =False
        self .project_tree_data =[]
        self .project_file_infos =[]
        self .code_file_infos =[]
    def ensure_project_index (self ,force :bool =False ):
        if not self .project_path :
            self .invalidate_project_cache ()
            return
        if self .project_index_ready and not force :
            return
        self .detected_languages =set ()
        self .project_file_infos =[]
        self .code_file_infos =[]
        self .project_tree_data =self ._scan_directory (self .project_path )
        self .project_index_ready =True
    def _scan_directory (self ,path :Path ):
        visible_entries =[]
        scanned_entries =[]
        try :
            with os .scandir (path )as iterator :
                for entry in iterator :
                    try :
                        is_dir =entry .is_dir (follow_symlinks =False )
                    except (OSError ,PermissionError ):
                        continue
                    scanned_entries .append ((not is_dir ,entry .name .lower (),entry ,is_dir ))
        except (OSError ,PermissionError ):
            return visible_entries
        scanned_entries .sort (key =lambda item :(item [0 ],item [1 ]))
        for _sort_key ,_name_key ,entry ,is_dir in scanned_entries :
            entry_path =Path (entry .path )
            is_visible_in_tree =not entry .name .startswith ('.')or entry .name =='.git'
            if is_dir :
                children =self ._scan_directory (entry_path )
                if is_visible_in_tree :
                    visible_entries .append ({
                    'name':entry .name ,
                    'display_name':entry .name ,
                    'path':entry_path ,
                    'ext':'',
                    'language':None ,
                    'is_dir':True ,
                    'is_code_file':False ,
                    'size':0 ,
                    'children':children ,
                    })
                continue
            ext =entry_path .suffix .lower ()
            is_code_file =ext in self .file_extensions
            language =self .file_extensions .get (ext )
            try :
                size =entry .stat (follow_symlinks =False ).st_size
            except (OSError ,PermissionError ):
                size =0
            file_info ={
            'name':entry .name ,
            'display_name':f'{entry .name } ({language })'if is_code_file else entry .name ,
            'path':entry_path ,
            'ext':ext ,
            'language':language ,
            'is_dir':False ,
            'is_code_file':is_code_file ,
            'size':size ,
            }
            self .project_file_infos .append (file_info )
            if is_code_file :
                self .code_file_infos .append (file_info )
                self .detected_languages .add (language )
            if is_visible_in_tree :
                visible_entries .append (file_info )
        return visible_entries
    def load_project_files (self ):
        self .file_tree .clear ()
        if not self .project_path :
            return
        self .ensure_project_index ()
        self .file_tree .blockSignals (True )
        self .file_tree .setUpdatesEnabled (False )
        root_item =QTreeWidgetItem (self .file_tree )
        root_item .setText (0 ,self .project_path .name )
        root_item .setCheckState (0 ,Qt .CheckState .Unchecked )
        root_item .setData (0 ,self .PATH_ROLE ,str (self .project_path ))
        root_item .setData (0 ,self .IS_DIR_ROLE ,True )
        root_item .setData (0 ,self .IS_CODE_FILE_ROLE ,False )
        self ._add_tree_nodes (root_item ,self .project_tree_data )
        self .file_tree .expandAll ()
        self .file_tree .setUpdatesEnabled (True )
        self .file_tree .blockSignals (False )
    def _add_tree_nodes (self ,parent_item ,entries ):
        for entry in entries :
            child_item =QTreeWidgetItem (parent_item )
            child_item .setText (0 ,entry ['display_name'])
            child_item .setCheckState (0 ,Qt .CheckState .Unchecked )
            child_item .setData (0 ,self .PATH_ROLE ,str (entry ['path']))
            child_item .setData (0 ,self .IS_DIR_ROLE ,entry ['is_dir'])
            child_item .setData (0 ,self .IS_CODE_FILE_ROLE ,entry .get ('is_code_file',False ))
            if entry ['is_dir']:
                child_item .setChildIndicatorPolicy (QTreeWidgetItem .ChildIndicatorPolicy .ShowIndicator )
                self ._add_tree_nodes (child_item ,entry .get ('children',[]))
    def on_item_changed (self ,item ,column ):
        if item .data (0 ,self .IS_DIR_ROLE ):
            new_state =item .checkState (0 )
            self .file_tree .blockSignals (True )
            self ._set_children_state (item ,new_state )
            self .file_tree .blockSignals (False )
        has_selected =self .has_selected_files ()
        self .process_btn .setEnabled (has_selected )
        self .delete_file_btn .setEnabled (has_selected )
    def _set_children_state (self ,parent_item ,state ):
        for i in range (parent_item .childCount ()):
            child =parent_item .child (i )
            child .setCheckState (0 ,state )
            if child .data (0 ,self .IS_DIR_ROLE ):
                self ._set_children_state (child ,state )
    def has_selected_files (self ):
        def check_item (item ):
            if item .checkState (0 )==Qt .CheckState .Checked and item .data (0 ,self .IS_CODE_FILE_ROLE ):
                return True
            for i in range (item .childCount ()):
                if check_item (item .child (i )):
                    return True
            return False
        for i in range (self .file_tree .topLevelItemCount ()):
            if check_item (self .file_tree .topLevelItem (i )):
                return True
        return False
    def get_selected_files (self ):
        selected =[]
        def collect_files (item ):
            if item .checkState (0 )==Qt .CheckState .Checked and item .data (0 ,self .IS_CODE_FILE_ROLE ):
                selected .append (Path (item .data (0 ,self .PATH_ROLE )))
            for i in range (item .childCount ()):
                collect_files (item .child (i ))
        for i in range (self .file_tree .topLevelItemCount ()):
            collect_files (self .file_tree .topLevelItem (i ))
        return selected
    def detect_languages (self ):
        if not self .project_path :
            self .detected_languages =set ()
            return
        self .ensure_project_index ()
        if self .detected_languages :
            languages_str =', '.join (sorted (self .detected_languages ))
            self .languages_label .setText (f'Языки: {languages_str }')
        else :
            self .languages_label .setText ('Языки: не определены')
    def select_all_files (self ):
        def set_checked (item ,state ):
            if item .data (0 ,self .IS_CODE_FILE_ROLE ):
                item .setCheckState (0 ,state )
            for i in range (item .childCount ()):
                set_checked (item .child (i ),state )
        state =Qt .CheckState .Checked
        for i in range (self .file_tree .topLevelItemCount ()):
            set_checked (self .file_tree .topLevelItem (i ),state )
    def deselect_all_files (self ):
        def set_unchecked (item ):
            item .setCheckState (0 ,Qt .CheckState .Unchecked )
            for i in range (item .childCount ()):
                set_unchecked (item .child (i ))
        for i in range (self .file_tree .topLevelItemCount ()):
            set_unchecked (self .file_tree .topLevelItem (i ))
    def process_files (self ):
        selected_files =self .get_selected_files ()
        if not selected_files :
            QMessageBox .warning (self ,'Предупреждение','Выберите файлы для обработки')
            return
        code_files =[f for f in selected_files if f .suffix .lower ()in self .file_extensions ]
        if not code_files :
            QMessageBox .warning (self ,'Предупреждение','Выбранные файлы не являются файлами с кодом. Обрабатываются только файлы с кодом.')
            return
        selected_files =code_files
        if not any ([self .remove_comments_cb .isChecked (),
        self .remove_empty_lines_cb .isChecked (),
        self .remove_trailing_spaces_cb .isChecked (),
        self .normalize_line_endings_cb .isChecked ()]):
            QMessageBox .warning (self ,'Предупреждение','Выберите хотя бы одну опцию очистки')
            return
        reply =QMessageBox .question (
        self ,'Подтверждение',
        f'Обработать {len (selected_files )} файл(ов)?',
        QMessageBox .StandardButton .Yes |QMessageBox .StandardButton .No
        )
        if reply !=QMessageBox .StandardButton .Yes :
            return
        self .progress_bar .setVisible (True )
        self .progress_bar .setMaximum (len (selected_files ))
        self .progress_bar .setValue (0 )
        processed =0
        errors_with_files =[]
        for idx ,file_path in enumerate (selected_files ):
            self .progress_bar .setValue (idx +1 )
            QApplication .processEvents ()
            original_content =None
            try :
                original_content =file_path .read_text (encoding ='utf-8',errors ='ignore')
                if self .backup_files_cb .isChecked ():
                    self .create_backup (file_path )
                content =original_content
                if self .remove_comments_cb .isChecked ():
                    content =self .remove_comments (content ,file_path )
                if self .remove_empty_lines_cb .isChecked ():
                    content =self .remove_empty_lines (content )
                if self .remove_trailing_spaces_cb .isChecked ():
                    content =self .remove_trailing_spaces (content )
                if self .normalize_line_endings_cb .isChecked ():
                    content =self .normalize_line_endings (content )
                error =None
                if self .verify_code_cb .isChecked ():
                    error =self .verify_code (file_path ,content )
                if error :
                    errors_with_files .append ((file_path ,error ,original_content ,content ))
                    self .log (f'⚠ Обнаружена ошибка в {file_path .name }: {error }')
                else :
                    if content !=original_content :
                        self .add_to_history (file_path ,original_content ,'Обработка')
                        file_path .write_text (content ,encoding ='utf-8')
                        processed +=1
                        self .log (f'✓ Обработан: {file_path .name }')
                    else :
                        self .log (f'○ Без изменений: {file_path .name }')
            except Exception as e :
                if original_content is None :
                    try :
                        original_content =file_path .read_text (encoding ='utf-8',errors ='ignore')
                    except Exception :
                        original_content =None
                errors_with_files .append ((file_path ,str (e ),original_content ,original_content ))
                self .log (f'✗ Ошибка при обработке {file_path .name }: {str (e )}')
        error_report_path =None
        if errors_with_files :
            error_report_path =self .create_error_report (errors_with_files )
        if self .create_resources_cb .isChecked ()and 'Python'in self .detected_languages :
            self .create_requirements_file ()
        self .progress_bar .setVisible (False )
        if self .project_path :
            self .update_statistics ()
        msg =f'Обработано файлов: {processed }'
        if errors_with_files :
            msg +=f'\nОшибок: {len (errors_with_files )}'
            if error_report_path is not None :
                msg +=f'\nОтчет: {error_report_path }'
        else :
            msg +='\nОшибок не обнаружено'
        QMessageBox .information (self ,'Результат',msg )
    def create_error_report (self ,errors_with_files )->Optional [Path ]:
        if not errors_with_files :
            return None
        report_dir =self .project_path if self .project_path else Path .cwd ()
        report_path =report_dir /'code_cleaner_errors.txt'
        timestamp =datetime .now ().strftime ('%Y-%m-%d %H:%M:%S')
        lines =[
        'Code Cleaner - Error Report',
        f'Timestamp: {timestamp }',
        f'Project: {self .project_path if self .project_path else report_dir }',
        f'Total errors: {len (errors_with_files )}',
        '',
        ]
        for index ,error_entry in enumerate (errors_with_files ,start =1 ):
            if len (error_entry )>=4 :
                file_path ,error_msg ,_original_content ,error_content =error_entry [:4 ]
            elif len (error_entry )==3 :
                file_path ,error_msg ,error_content =error_entry
            elif len (error_entry )==2 :
                file_path ,error_msg =error_entry
                error_content =None
            else :
                continue
            line_number ,error_line =self .get_error_line_details (str (error_msg ),error_content )
            lines .extend ([
            f'{index }. File: {file_path }',
            f'   Error: {error_msg }',
            ])
            if line_number is not None :
                lines .append (f'   Line: {line_number }')
            if error_line is not None :
                lines .append (f'   Code: {error_line }')
            lines .append ('')
        try :
            report_path .write_text ('\n'.join (lines ),encoding ='utf-8')
            self .log (f'Report created: {report_path }')
            return report_path
        except Exception as e :
            self .log (f'Failed to create error report: {str (e )}')
            return None
    def get_error_line_details (self ,error_msg :str ,content :Optional [str ])->Tuple [Optional [int ],Optional [str ]]:
        line_number =None
        for pattern in (r'строке\s+(\d+)',r'line\s+(\d+)',r'lineno=(\d+)'):
            match =re .search (pattern ,error_msg ,re .IGNORECASE )
            if match :
                try :
                    line_number =int (match .group (1 ))
                except ValueError :
                    line_number =None
                break
        if line_number is None or content is None :
            return line_number ,None
        content_lines =content .split ('\n')
        if 1 <=line_number <=len (content_lines ):
            return line_number ,content_lines [line_number -1 ].rstrip ()
        return line_number ,None
    def create_requirements_file (self ):
        if not self .project_path :
            return
        self .ensure_project_index ()
        dependencies =set ()
        stdlib_modules ={
        'sys','os','re','pathlib','typing','collections','datetime',
        'json','xml','urllib','http','email','sqlite3','csv',
        'logging','unittest','threading','multiprocessing','asyncio',
        'itertools','functools','operator','copy','pickle','hashlib',
        'base64','random','math','statistics','decimal','fractions',
        'string','textwrap','unicodedata','locale','gettext','argparse',
        'configparser','shutil','tempfile','glob','fnmatch','linecache',
        'codecs','io','gzip','bz2','lzma','zipfile','tarfile',
        'struct','array','ctypes','mmap','select','selectors',
        'socket','ssl','socketserver','queue','sched','time','calendar',
        'locale','gettext','argparse','getopt','logging','warnings',
        'dataclasses','enum','types','weakref','gc','inspect','ast',
        'dis','pdb','profile','pstats','timeit','trace','tracemalloc',
        'faulthandler','pydoc','doctest','unittest','test','lib2to3',
        'distutils','ensurepip','venv','zipapp','compileall','py_compile',
        'keyword','token','tokenize','tabnanny','pyclbr','py_compile',
        'compileall','dis','pickletools','formatter','msilib','msvcrt',
        'winreg','winsound','posix','pwd','spwd','grp','crypt',
        'termios','tty','pty','fcntl','pipes','resource','nis',
        'syslog','platform','errno','signal','subprocess','sched',
        'queue','select','selectors','asyncio','concurrent','multiprocessing',
        'threading','_thread','dummy_threading','queue','contextvars',
        'traceback','builtins','__builtin__','future_builtins','copyreg'
        }
        python_files =[info ['path']for info in self .project_file_infos if info ['ext']=='.py']
        import_pattern =re .compile (r'^(?:from\s+(\S+)\s+)?import\s+(\S+)',re .MULTILINE )
        for py_file in python_files :
            if '__pycache__'in str (py_file )or '.pyc'in str (py_file ):
                continue
            try :
                content =py_file .read_text (encoding ='utf-8',errors ='ignore')
                matches =import_pattern .findall (content )
                for from_module ,import_module in matches :
                    if from_module :
                        module =from_module .split ('.')[0 ]
                    else :
                        module =import_module .split ('.')[0 ].split (' as ')[0 ]
                    if module and not module .startswith ('.')and module not in stdlib_modules :
                        dependencies .add (module )
            except Exception :
                continue
        if not dependencies and 'Python'in self .detected_languages :
            for py_file in python_files :
                if '__pycache__'in str (py_file ):
                    continue
                try :
                    content =py_file .read_text (encoding ='utf-8',errors ='ignore')
                    if 'PyQt6'in content or 'from PyQt6'in content or 'import PyQt6'in content :
                        dependencies .add ('PyQt6')
                        break
                except Exception :
                    continue
        if not dependencies and 'Python'in self .detected_languages :
            dependencies .add ('PyQt6')
        dependencies_list =sorted (dependencies )
        requirements_file =self .project_path /'requirements.txt'
        if dependencies_list :
            requirements_file .write_text ('\n'.join (dependencies_list ),encoding ='utf-8')
            self .log (f'✓ Создан файл requirements.txt с зависимостями: {", ".join (dependencies_list )}')
        else :
            self .log ('⚠ Не найдено зависимостей для requirements.txt')
    def delete_selected_files (self ):
        selected_files =self .get_selected_files ()
        if not selected_files :
            QMessageBox .warning (self ,'Предупреждение','Выберите файлы для удаления')
            return
        reply =QMessageBox .question (
        self ,'Подтверждение удаления',
        f'Удалить {len (selected_files )} файл(ов)?\n\nЭто действие нельзя отменить!',
        QMessageBox .StandardButton .Yes |QMessageBox .StandardButton .No ,
        QMessageBox .StandardButton .No
        )
        if reply !=QMessageBox .StandardButton .Yes :
            return
        deleted =0
        errors =[]
        for file_path in selected_files :
            try :
                file_path .unlink ()
                deleted +=1
                self .log (f'🗑️ Удален: {file_path .name }')
            except Exception as e :
                errors .append (f'{file_path .name }: {str (e )}')
        self .invalidate_project_cache ()
        self .load_project_files ()
        self .detect_languages ()
        self .update_statistics ()
        msg =f'Удалено файлов: {deleted }'
        if errors :
            msg +=f'\nОшибок: {len (errors )}'
        QMessageBox .information (self ,'Результат',msg )
    def update_statistics (self ):
        if not self .project_path :
            self .stats_table .setRowCount (0 )
            return
        self .ensure_project_index ()
        self .stats_table .setRowCount (1 )
        self .stats_table .setItem (0 ,0 ,QTableWidgetItem ('Статистика'))
        self .stats_table .setItem (0 ,1 ,QTableWidgetItem ('Загрузка...'))
        self .stats_table .resizeColumnsToContents ()
        if self .stats_worker and self .stats_worker .isRunning ():
            self .stats_worker .requestInterruption ()
            self .stats_worker .wait (100 )
        self .stats_worker =ProjectStatisticsWorker (
        str (self .project_path ),
        [dict (info )for info in self .project_file_infos ],
        self ._calculate_statistics_from_files ,
        self
        )
        self .stats_worker .stats_ready .connect (self ._apply_statistics_result )
        self .stats_worker .start ()
    def calculate_statistics (self )->dict :
        if not self .project_path :
            return {}
        self .ensure_project_index ()
        return self ._calculate_statistics_from_files ([dict (info )for info in self .project_file_infos ])
    def _calculate_statistics_from_files (self ,file_infos :List [Dict ],worker =None )->dict :
        total_files =0
        total_lines =0
        total_lines_no_comments =0
        total_comments =0
        total_functions =0
        total_classes =0
        total_size =0
        files_by_language ={}
        for file_info in file_infos :
            if worker and worker .isInterruptionRequested ():
                return {}
            file_path =file_info ['path']
            if '__pycache__'in str (file_path ):
                continue
            total_size +=file_info .get ('size',0 )
            if not file_info .get ('is_code_file'):
                continue
            try :
                ext =file_info ['ext']
                lang =file_info ['language']
                files_by_language [lang ]=files_by_language .get (lang ,0 )+1
                total_files +=1
                content =file_path .read_text (encoding ='utf-8',errors ='ignore')
                lines =content .split ('\n')
                total_lines +=len (lines )
                for line in lines :
                    stripped =line .strip ()
                    if stripped .startswith ('#'):
                        total_comments +=1
                    elif ext =='.py':
                        if stripped .startswith ('def ')or stripped .startswith ('async def '):
                            total_functions +=1
                        elif stripped .startswith ('class '):
                            total_classes +=1
                cleaned =self .remove_comments (content ,file_path )
                total_lines_no_comments +=len (cleaned .split ('\n'))
            except Exception :
                continue
        comment_percentage =(total_comments /total_lines *100 )if total_lines >0 else 0
        stats ={
        'Всего файлов':total_files ,
        'Всего строк кода':total_lines ,
        'Строк без комментариев':total_lines_no_comments ,
        'Строк комментариев':total_comments ,
        'Процент комментариев':f'{comment_percentage :.2f}%',
        'Функций (Python)':total_functions ,
        'Классов (Python)':total_classes ,
        'Общий размер':f'{total_size /1024 :.2f} KB',
        'Файлов по языкам':', '.join ([f'{k }: {v }'for k ,v in files_by_language .items ()])
        }
        return stats
    def _apply_statistics_result (self ,project_token :str ,stats :dict ):
        if not self .project_path or str (self .project_path )!=project_token :
            return
        if not stats :
            self .stats_table .setRowCount (0 )
            return
        self .stats_table .setRowCount (len (stats ))
        for row ,(key ,value )in enumerate (stats .items ()):
            self .stats_table .setItem (row ,0 ,QTableWidgetItem (str (key )))
            self .stats_table .setItem (row ,1 ,QTableWidgetItem (str (value )))
        self .stats_table .resizeColumnsToContents ()
    def load_settings (self ):
        if self .settings_file .exists ():
            try :
                with open (self .settings_file ,'r',encoding ='utf-8')as f :
                    data =json .load (f )
                    self .settings_profiles =data .get ('profiles',{'default':{}})
                    self .current_profile =data .get ('current_profile','default')
            except Exception :
                self .settings_profiles ={'default':{}}
        else :
            self .settings_profiles ={'default':{}}
    def save_settings (self ):
        try :
            data ={
            'profiles':self .settings_profiles ,
            'current_profile':self .current_profile
            }
            with open (self .settings_file ,'w',encoding ='utf-8')as f :
                json .dump (data ,f ,indent =2 ,ensure_ascii =False )
        except Exception :
            pass
    def load_history (self ):
        if self .history_file .exists ():
            try :
                with open (self .history_file ,'r',encoding ='utf-8')as f :
                    self .history =json .load (f )
            except Exception :
                self .history =[]
        else :
            self .history =[]
        self .refresh_history ()
    def save_history (self ):
        try :
            self .history =self .history [-100 :]
            with open (self .history_file ,'w',encoding ='utf-8')as f :
                json .dump (self .history ,f ,indent =2 ,ensure_ascii =False )
        except Exception :
            pass
    def add_to_history (self ,file_path :Path ,original_content :str ,action :str ):
        history_entry ={
        'timestamp':datetime .now ().isoformat (),
        'file':str (file_path ),
        'action':action ,
        'content':original_content [:1000 ]
        }
        self .history .append (history_entry )
        self .save_history ()
        self .refresh_history ()
    def refresh_history (self ):
        self .history_list .clear ()
        for entry in reversed (self .history [-50 :]):
            timestamp =datetime .fromisoformat (entry ['timestamp']).strftime ('%Y-%m-%d %H:%M:%S')
            item_text =f"{timestamp } - {Path (entry ['file']).name } - {entry ['action']}"
            item =QListWidgetItem (item_text )
            item .setData (Qt .ItemDataRole .UserRole ,entry )
            self .history_list .addItem (item )
    def restore_from_history (self ):
        current_item =self .history_list .currentItem ()
        if not current_item :
            QMessageBox .warning (self ,'Предупреждение','Выберите запись из истории')
            return
        entry =current_item .data (Qt .ItemDataRole .UserRole )
        if not entry :
            return
        file_path =Path (entry ['file'])
        if not file_path .exists ():
            QMessageBox .warning (self ,'Ошибка','Файл не существует')
            return
        reply =QMessageBox .question (
        self ,'Подтверждение',
        f'Восстановить файл {file_path .name } из истории?',
        QMessageBox .StandardButton .Yes |QMessageBox .StandardButton .No
        )
        if reply ==QMessageBox .StandardButton .Yes :
            try :
                backup_path =file_path .with_suffix (file_path .suffix +'.backup')
                if backup_path .exists ():
                    content =backup_path .read_text (encoding ='utf-8')
                    file_path .write_text (content ,encoding ='utf-8')
                    self .log (f'↩️ Восстановлен из истории: {file_path .name }')
                else :
                    QMessageBox .warning (self ,'Ошибка','Резервная копия не найдена')
            except Exception as e :
                QMessageBox .critical (self ,'Ошибка',f'Не удалось восстановить файл: {str (e )}')
    def clear_history (self ):
        reply =QMessageBox .question (
        self ,'Подтверждение',
        'Очистить всю историю?',
        QMessageBox .StandardButton .Yes |QMessageBox .StandardButton .No
        )
        if reply ==QMessageBox .StandardButton .Yes :
            self .history =[]
            self .save_history ()
            self .refresh_history ()
    def save_current_profile (self ):
        profile_name =self .profile_combo .currentText ()
        if not profile_name :
            profile_name ='default'
        profile ={
        'remove_comments':self .remove_comments_cb .isChecked (),
        'remove_empty_lines':self .remove_empty_lines_cb .isChecked (),
        'verify_code':self .verify_code_cb .isChecked (),
        'create_resources':self .create_resources_cb .isChecked (),
        'remove_trailing_spaces':self .remove_trailing_spaces_cb .isChecked (),
        'normalize_line_endings':self .normalize_line_endings_cb .isChecked (),
        'backup_files':self .backup_files_cb .isChecked (),
        }
        self .settings_profiles [profile_name ]=profile
        self .save_settings ()
        self .profile_combo .clear ()
        self .profile_combo .addItems (list (self .settings_profiles .keys ()))
        self .profile_combo .setCurrentText (profile_name )
        QMessageBox .information (self ,'Успех',f'Профиль "{profile_name }" сохранен')
    def load_profile (self ,profile_name :str ):
        if profile_name in self .settings_profiles :
            profile =self .settings_profiles [profile_name ]
            self .remove_comments_cb .setChecked (profile .get ('remove_comments',False ))
            self .remove_empty_lines_cb .setChecked (profile .get ('remove_empty_lines',False ))
            self .verify_code_cb .setChecked (profile .get ('verify_code',False ))
            self .create_resources_cb .setChecked (profile .get ('create_resources',False ))
            self .remove_trailing_spaces_cb .setChecked (profile .get ('remove_trailing_spaces',False ))
            self .normalize_line_endings_cb .setChecked (profile .get ('normalize_line_endings',False ))
            self .backup_files_cb .setChecked (profile .get ('backup_files',False ))
            self .current_profile =profile_name
    def create_new_profile (self ):
        name ,ok =QInputDialog .getText (self ,'Новый профиль','Введите имя профиля:')
        if ok and name :
            if name not in self .settings_profiles :
                self .settings_profiles [name ]={}
                self .save_settings ()
                self .profile_combo .addItem (name )
                self .profile_combo .setCurrentText (name )
                QMessageBox .information (self ,'Успех',f'Профиль "{name }" создан')
            else :
                QMessageBox .warning (self ,'Ошибка','Профиль с таким именем уже существует')
    def delete_profile (self ):
        profile_name =self .profile_combo .currentText ()
        if profile_name =='default':
            QMessageBox .warning (self ,'Ошибка','Нельзя удалить профиль по умолчанию')
            return
        reply =QMessageBox .question (
        self ,'Подтверждение',
        f'Удалить профиль "{profile_name }"?',
        QMessageBox .StandardButton .Yes |QMessageBox .StandardButton .No
        )
        if reply ==QMessageBox .StandardButton .Yes :
            del self .settings_profiles [profile_name ]
            self .save_settings ()
            self .profile_combo .clear ()
            self .profile_combo .addItems (list (self .settings_profiles .keys ()))
            self .profile_combo .setCurrentText ('default')
    def export_profile (self ):
        profile_name =self .profile_combo .currentText ()
        if profile_name not in self .settings_profiles :
            QMessageBox .warning (self ,'Ошибка','Профиль не найден')
            return
        file_path ,_ =QFileDialog .getSaveFileName (
        self ,'Экспорт профиля',f'{profile_name }.json','Файлы JSON (*.json)'
        )
        if file_path :
            try :
                data ={
                'profile_name':profile_name ,
                'settings':self .settings_profiles [profile_name ]
                }
                with open (file_path ,'w',encoding ='utf-8')as f :
                    json .dump (data ,f ,indent =2 ,ensure_ascii =False )
                QMessageBox .information (self ,'Успех','Профиль экспортирован')
            except Exception as e :
                QMessageBox .critical (self ,'Ошибка',f'Не удалось экспортировать: {str (e )}')
    def import_profile (self ):
        file_path ,_ =QFileDialog .getOpenFileName (
        self ,'Импорт профиля','','Файлы JSON (*.json)'
        )
        if file_path :
            try :
                with open (file_path ,'r',encoding ='utf-8')as f :
                    data =json .load (f )
                profile_name =data .get ('profile_name','imported')
                if profile_name in self .settings_profiles :
                    reply =QMessageBox .question (
                    self ,'Подтверждение',
                    f'Профиль "{profile_name }" уже существует. Перезаписать?',
                    QMessageBox .StandardButton .Yes |QMessageBox .StandardButton .No
                    )
                    if reply !=QMessageBox .StandardButton .Yes :
                        return
                self .settings_profiles [profile_name ]=data .get ('settings',{})
                self .save_settings ()
                self .profile_combo .clear ()
                self .profile_combo .addItems (list (self .settings_profiles .keys ()))
                self .profile_combo .setCurrentText (profile_name )
                QMessageBox .information (self ,'Успех','Профиль импортирован')
            except Exception as e :
                QMessageBox .critical (self ,'Ошибка',f'Не удалось импортировать: {str (e )}')
    def setup_shortcuts (self ):
        QShortcut (QKeySequence ("Ctrl+О"),self ,self .open_folder )
        QShortcut (QKeySequence ("Ctrl+А"),self ,self .select_all_files )
        QShortcut (QKeySequence ("Ctrl+D"),self ,self .deselect_all_files )
        QShortcut (QKeySequence ("Ctrl+R"),self ,self .process_files )
        QShortcut (QKeySequence ("Ctrl+S"),self ,self .save_current_profile )
        QShortcut (QKeySequence ("F5"),self ,self .update_statistics )
    def log (self ,message :str ):
        self .log_text .append (message )
        self .log_text .verticalScrollBar ().setValue (
        self .log_text .verticalScrollBar ().maximum ()
        )
def get_resource_path (relative_path ):
    try :
        base_path =Path (sys ._MEIPASS )
    except Exception :
        base_path =Path (__file__ ).parent
    return base_path /relative_path
def find_resource_path (*relative_paths ):
    for relative_path in relative_paths :
        candidate =get_resource_path (relative_path )
        if candidate .exists ():
            return candidate
    return get_resource_path (relative_paths [0 ])if relative_paths else Path ()
def main ():
    app =QApplication (sys .argv )
    app .setStyle ('Fusion')
    icon_path =find_resource_path ('Code Cleaner.ico','Code Cleaner.png','Код Очиститель.png')
    if icon_path .exists ():
        app .setWindowIcon (QIcon (str (icon_path )))
    window =CodeCleanerApp ()
    if icon_path .exists ():
        window .setWindowIcon (QIcon (str (icon_path )))
    window .show ()
    app .processEvents ()
    sys .exit (app .exec ())
if __name__ =='__main__':
    main ()