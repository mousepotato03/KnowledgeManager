#!/usr/bin/env python3
"""
GUI Interface for RAG Knowledge Indexing
A user-friendly tkinter-based interface for managing FlowGenius tool knowledge
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False
import threading
import asyncio
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
import json
import datetime

from rag_indexer import RAGProcessor, ProcessingConfig
from loguru import logger


class RAGUploaderGUI:
    """Main GUI application for RAG knowledge uploading"""
    
    def __init__(self, root):
        self.root = root
        self.dnd_enabled = DND_AVAILABLE
        self.root.title("FlowGenius RAG Knowledge Uploader")
        self.root.geometry("800x700")
        
        # Application state
        self.processor = None
        self.tools_data = []
        self.current_operation = None
        
        # Setup GUI
        self.setup_styles()
        self.create_widgets()
        self.setup_logging()
        
        # Initialize processor in background
        self.root.after(100, self.initialize_processor)
    
    def setup_styles(self):
        """Setup ttk styles for better UI"""
        style = ttk.Style()
        
        # Configure styles for better appearance
        style.configure("Title.TLabel", font=("Arial", 16, "bold"))
        style.configure("Section.TLabel", font=("Arial", 12, "bold"))
        style.configure("Success.TLabel", foreground="green", font=("Arial", 10, "bold"))
        style.configure("Error.TLabel", foreground="red", font=("Arial", 10, "bold"))
        style.configure("Warning.TLabel", foreground="orange", font=("Arial", 10, "bold"))
    
    def create_widgets(self):
        """Create and layout all GUI widgets"""
        
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="RAG Knowledge Uploader", style="Title.TLabel")
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Tool selection section
        self.create_tool_selection_section(main_frame, 1)
        
        # Document input section
        self.create_document_input_section(main_frame, 2)
        
        # Processing options section
        self.create_processing_options_section(main_frame, 3)
        
        # Action buttons section
        self.create_action_buttons_section(main_frame, 4)
        
        # Progress and log section
        self.create_progress_log_section(main_frame, 5)
        
        # Status bar
        self.create_status_bar(main_frame, 6)
    
    def create_tool_selection_section(self, parent, row):
        """Create tool selection widgets"""
        section_frame = ttk.LabelFrame(parent, text="도구 선택", padding="10")
        section_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        section_frame.columnconfigure(1, weight=1)
        
        # Tool selection
        ttk.Label(section_frame, text="도구:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        
        self.tool_combobox = ttk.Combobox(section_frame, state="readonly", width=50)
        self.tool_combobox.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        self.refresh_tools_btn = ttk.Button(section_frame, text="새로고침", command=self.refresh_tools)
        self.refresh_tools_btn.grid(row=0, column=2, sticky=tk.E)
        
        # Tool info display
        self.tool_info_text = tk.Text(section_frame, height=3, wrap=tk.WORD, state=tk.DISABLED)
        self.tool_info_text.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Bind tool selection event
        self.tool_combobox.bind('<<ComboboxSelected>>', self.on_tool_selected)
    
    def create_document_input_section(self, parent, row):
        """Create document input widgets"""
        section_frame = ttk.LabelFrame(parent, text="문서 입력", padding="10")
        section_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        section_frame.columnconfigure(1, weight=1)
        
        # Source type selection
        ttk.Label(section_frame, text="소스 타입:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        
        self.source_type_var = tk.StringVar(value="file")
        source_frame = ttk.Frame(section_frame)
        source_frame.grid(row=0, column=1, columnspan=2, sticky=(tk.W, tk.E))
        
        ttk.Radiobutton(source_frame, text="파일", variable=self.source_type_var, 
                       value="file", command=self.on_source_type_changed).pack(side=tk.LEFT, padx=(0, 20))
        ttk.Radiobutton(source_frame, text="URL", variable=self.source_type_var, 
                       value="url", command=self.on_source_type_changed).pack(side=tk.LEFT)
        
        # Drag and drop area
        self.create_drag_drop_area(section_frame, row=1)
        
        # File/URL input
        ttk.Label(section_frame, text="파일/URL:").grid(row=2, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        
        self.source_path_var = tk.StringVar()
        self.source_path_entry = ttk.Entry(section_frame, textvariable=self.source_path_var, width=50)
        self.source_path_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=(10, 0))
        
        self.browse_btn = ttk.Button(section_frame, text="찾아보기", command=self.browse_file)
        self.browse_btn.grid(row=2, column=2, sticky=tk.E, pady=(10, 0))
        
        # Document title
        ttk.Label(section_frame, text="제목 (선택):").grid(row=3, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        
        self.title_var = tk.StringVar()
        ttk.Entry(section_frame, textvariable=self.title_var, width=50).grid(row=3, column=1, columnspan=2, 
                                                                           sticky=(tk.W, tk.E), pady=(10, 0))
    
    def create_drag_drop_area(self, parent, row):
        """Create drag and drop area for file upload"""
        # Create drag and drop frame
        self.dnd_frame = tk.Frame(parent, height=100, bg='#f0f0f0', relief='groove', bd=2)
        self.dnd_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        self.dnd_frame.grid_propagate(False)
        
        # Create label for drag and drop instructions
        self.dnd_label = tk.Label(
            self.dnd_frame, 
            text="📁 여기에 파일을 드래그하세요\n(PDF, TXT, MD 파일 지원)",
            bg='#f0f0f0',
            fg='#666666',
            font=('Arial', 12),
            justify=tk.CENTER
        )
        self.dnd_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # Enable drag and drop if available
        if self.dnd_enabled:
            try:
                self.dnd_frame.drop_target_register(DND_FILES)
                self.dnd_frame.dnd_bind('<<Drop>>', self.on_file_drop)
                self.dnd_frame.dnd_bind('<<DragEnter>>', self.on_drag_enter)
                self.dnd_frame.dnd_bind('<<DragLeave>>', self.on_drag_leave)
            except Exception as e:
                logger.warning(f"드래그 앤 드롭 초기화 실패: {e}")
                self.dnd_enabled = False
        
        if not self.dnd_enabled:
            self.dnd_label.config(text="📁 파일 찾아보기 버튼을 사용하세요\n(드래그 앤 드롭 라이브러리 미설치)")
    
    def on_file_drop(self, event):
        """Handle file drop event"""
        try:
            # Get dropped files
            files = self.root.tk.splitlist(event.data)
            
            if not files:
                return
            
            # Take the first file
            file_path = files[0]
            
            # Check if it's a supported file type
            supported_extensions = ['.pdf', '.txt', '.md', '.markdown']
            file_ext = Path(file_path).suffix.lower()
            
            if file_ext not in supported_extensions:
                messagebox.showwarning(
                    "지원되지 않는 파일", 
                    f"지원되는 파일 형식: {', '.join(supported_extensions)}\n선택된 파일: {file_ext}"
                )
                return
            
            # Set the file path
            self.source_path_var.set(file_path)
            
            # Auto-suggest title from filename
            if not self.title_var.get():
                title = Path(file_path).stem
                self.title_var.set(title)
            
            # Set source type to file
            self.source_type_var.set("file")
            self.on_source_type_changed()
            
            # Update drag and drop area appearance
            self.dnd_label.config(
                text=f"✅ 파일 선택됨:\n{Path(file_path).name}",
                fg='#008000'
            )
            
            logger.info(f"파일이 드래그 앤 드롭되었습니다: {file_path}")
            
        except Exception as e:
            logger.error(f"파일 드롭 처리 오류: {e}")
            messagebox.showerror("파일 드롭 오류", f"파일 처리 중 오류가 발생했습니다:\n{e}")
        
        # Reset drag and drop area appearance
        self.reset_dnd_appearance()
    
    def on_drag_enter(self, event):
        """Handle drag enter event"""
        if self.source_type_var.get() == "file":
            self.dnd_frame.config(bg='#e6f3ff', relief='solid')
            self.dnd_label.config(
                bg='#e6f3ff',
                text="📂 파일을 놓아주세요",
                fg='#0066cc'
            )
    
    def on_drag_leave(self, event):
        """Handle drag leave event"""
        self.reset_dnd_appearance()
    
    def reset_dnd_appearance(self):
        """Reset drag and drop area to default appearance"""
        if hasattr(self, 'source_path_var') and self.source_path_var.get():
            # File is selected, show selected state
            file_path = self.source_path_var.get()
            self.dnd_frame.config(bg='#f0f8f0', relief='solid')
            self.dnd_label.config(
                bg='#f0f8f0',
                text=f"✅ 파일 선택됨:\n{Path(file_path).name}",
                fg='#008000'
            )
        else:
            # No file selected, show default state
            self.dnd_frame.config(bg='#f0f0f0', relief='groove')
            if self.dnd_enabled:
                self.dnd_label.config(
                    bg='#f0f0f0',
                    text="📁 여기에 파일을 드래그하세요\n(PDF, TXT, MD 파일 지원)",
                    fg='#666666'
                )
            else:
                self.dnd_label.config(
                    bg='#f0f0f0',
                    text="📁 파일 찾아보기 버튼을 사용하세요\n(드래그 앤 드롭 라이브러리 미설치)",
                    fg='#666666'
                )
    
    def create_processing_options_section(self, parent, row):
        """Create processing options widgets"""
        section_frame = ttk.LabelFrame(parent, text="처리 옵션", padding="10")
        section_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        options_frame = ttk.Frame(section_frame)
        options_frame.pack(fill=tk.X)
        
        # Chunk size
        ttk.Label(options_frame, text="청크 크기:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.chunk_size_var = tk.StringVar(value="1000")
        ttk.Entry(options_frame, textvariable=self.chunk_size_var, width=10).grid(row=0, column=1, padx=(0, 20))
        
        # Chunk overlap
        ttk.Label(options_frame, text="청크 겹침:").grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        self.chunk_overlap_var = tk.StringVar(value="200")
        ttk.Entry(options_frame, textvariable=self.chunk_overlap_var, width=10).grid(row=0, column=3, padx=(0, 20))
        
        # Batch size
        ttk.Label(options_frame, text="배치 크기:").grid(row=0, column=4, sticky=tk.W, padx=(0, 10))
        self.batch_size_var = tk.StringVar(value="10")
        ttk.Entry(options_frame, textvariable=self.batch_size_var, width=10).grid(row=0, column=5)
    
    def create_action_buttons_section(self, parent, row):
        """Create action buttons"""
        section_frame = ttk.Frame(parent)
        section_frame.grid(row=row, column=0, columnspan=3, pady=(0, 10))
        
        # Upload button
        self.upload_btn = ttk.Button(section_frame, text="📤 업로드 시작", 
                                   command=self.start_upload, style="Accent.TButton")
        self.upload_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # View stats button
        self.stats_btn = ttk.Button(section_frame, text="📊 통계 보기", 
                                  command=self.show_tool_stats)
        self.stats_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Cleanup button
        self.cleanup_btn = ttk.Button(section_frame, text="🗑️ 정리", 
                                    command=self.cleanup_knowledge)
        self.cleanup_btn.pack(side=tk.LEFT)
        
        # Stop button (initially disabled)
        self.stop_btn = ttk.Button(section_frame, text="⏹️ 중지", 
                                 command=self.stop_operation, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.RIGHT)
    
    def create_progress_log_section(self, parent, row):
        """Create progress bar and log display"""
        section_frame = ttk.LabelFrame(parent, text="진행 상황 및 로그", padding="10")
        section_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        section_frame.columnconfigure(0, weight=1)
        section_frame.rowconfigure(1, weight=1)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(section_frame, variable=self.progress_var, 
                                          maximum=100, length=400)
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Log text area
        self.log_text = scrolledtext.ScrolledText(section_frame, height=15, wrap=tk.WORD)
        self.log_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure text tags for different log levels
        self.log_text.tag_configure("INFO", foreground="black")
        self.log_text.tag_configure("SUCCESS", foreground="green", font=("Arial", 10, "bold"))
        self.log_text.tag_configure("WARNING", foreground="orange")
        self.log_text.tag_configure("ERROR", foreground="red", font=("Arial", 10, "bold"))
    
    def create_status_bar(self, parent, row):
        """Create status bar"""
        self.status_var = tk.StringVar(value="준비")
        status_bar = ttk.Label(parent, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
    
    def setup_logging(self):
        """Setup logging to display in GUI"""
        class GUILogHandler:
            def __init__(self, gui):
                self.gui = gui
            
            def write(self, record):
                # Extract log level and message
                level = record.record["level"].name
                message = record.record["message"]
                
                # Schedule GUI update in main thread
                self.gui.root.after(0, self.gui.add_log_message, level, message)
        
        # Remove existing handlers and add GUI handler
        logger.remove()
        logger.add(GUILogHandler(self).write, level="DEBUG")
    
    def add_log_message(self, level: str, message: str):
        """Add a log message to the GUI log display"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_line = f"[{timestamp}] {message}\n"
        
        # Insert at end with appropriate tag
        self.log_text.insert(tk.END, log_line, level)
        self.log_text.see(tk.END)
    
    def initialize_processor(self):
        """Initialize the RAG processor in background"""
        def init():
            try:
                self.processor = RAGProcessor()
                self.root.after(0, self.on_processor_ready)
            except Exception as e:
                self.root.after(0, lambda: self.on_processor_error(str(e)))
        
        threading.Thread(target=init, daemon=True).start()
        self.update_status("RAG 프로세서 초기화 중...")
    
    def on_processor_ready(self):
        """Called when RAG processor is ready"""
        self.update_status("준비 완료")
        self.refresh_tools()
        logger.info("RAG 프로세서 초기화 완료")
    
    def on_processor_error(self, error: str):
        """Called when processor initialization fails"""
        self.update_status(f"초기화 실패: {error}")
        logger.error(f"RAG 프로세서 초기화 실패: {error}")
        messagebox.showerror("초기화 오류", f"RAG 프로세서 초기화에 실패했습니다:\n{error}")
    
    def refresh_tools(self):
        """Refresh the list of available tools"""
        if not self.processor:
            return
        
        def fetch_tools():
            try:
                result = self.processor.supabase.table("tools").select(
                    "id,name,description,categories"
                ).eq("is_active", True).order("name").execute()
                
                self.tools_data = result.data if result.data else []
                self.root.after(0, self.update_tool_combobox)
                
            except Exception as e:
                self.root.after(0, lambda: logger.error(f"도구 목록 가져오기 실패: {e}"))
        
        threading.Thread(target=fetch_tools, daemon=True).start()
        self.update_status("도구 목록 새로고침 중...")
    
    def update_tool_combobox(self):
        """Update the tool combobox with fetched data"""
        tool_names = [f"{tool['name']} ({tool['id'][:8]}...)" for tool in self.tools_data]
        self.tool_combobox['values'] = tool_names
        
        if tool_names:
            self.tool_combobox.current(0)
            self.on_tool_selected()
        
        self.update_status(f"{len(tool_names)}개 도구 로드됨")
        logger.info(f"{len(tool_names)}개 도구를 불러왔습니다")
    
    def on_tool_selected(self, event=None):
        """Handle tool selection change"""
        selection = self.tool_combobox.current()
        if selection >= 0 and selection < len(self.tools_data):
            tool = self.tools_data[selection]
            
            # Update tool info display
            self.tool_info_text.config(state=tk.NORMAL)
            self.tool_info_text.delete(1.0, tk.END)
            
            info = f"ID: {tool['id']}\n"
            info += f"카테고리: {', '.join(tool.get('categories', []))}\n"
            info += f"설명: {tool.get('description', '설명 없음')}"
            
            self.tool_info_text.insert(1.0, info)
            self.tool_info_text.config(state=tk.DISABLED)
    
    def on_source_type_changed(self):
        """Handle source type change"""
        if self.source_type_var.get() == "file":
            self.browse_btn.config(text="찾아보기", command=self.browse_file)
        else:
            self.browse_btn.config(text="URL 확인", command=self.validate_url)
    
    def browse_file(self):
        """Open file dialog to select a document"""
        filetypes = [
            ("모든 지원 파일", "*.pdf;*.txt;*.md;*.markdown"),
            ("PDF 파일", "*.pdf"),
            ("텍스트 파일", "*.txt"),
            ("마크다운 파일", "*.md;*.markdown"),
            ("모든 파일", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="문서 파일 선택",
            filetypes=filetypes
        )
        
        if filename:
            self.source_path_var.set(filename)
            
            # Auto-suggest title from filename
            if not self.title_var.get():
                title = Path(filename).stem
                self.title_var.set(title)
            
            # Update drag and drop area appearance
            if hasattr(self, 'reset_dnd_appearance'):
                self.reset_dnd_appearance()
    
    def validate_url(self):
        """Validate the entered URL"""
        url = self.source_path_var.get().strip()
        if not url:
            messagebox.showwarning("URL 필요", "URL을 입력해주세요")
            return
        
        if not url.startswith(('http://', 'https://')):
            self.source_path_var.set('https://' + url)
        
        messagebox.showinfo("URL 확인", f"URL이 설정되었습니다:\n{self.source_path_var.get()}")
    
    def start_upload(self):
        """Start the upload process"""
        # Validate inputs
        if not self.validate_inputs():
            return
        
        # Get selected tool
        tool_index = self.tool_combobox.current()
        tool = self.tools_data[tool_index]
        
        # Get processing config
        try:
            config = ProcessingConfig(
                chunk_size=int(self.chunk_size_var.get()),
                chunk_overlap=int(self.chunk_overlap_var.get()),
                batch_size=int(self.batch_size_var.get())
            )
        except ValueError:
            messagebox.showerror("입력 오류", "처리 옵션에 올바른 숫자를 입력해주세요")
            return
        
        # Prepare upload parameters
        upload_params = {
            'source_path': self.source_path_var.get().strip(),
            'tool_id': tool['id'],
            'source_type': self.detect_source_type(),
            'custom_title': self.title_var.get().strip() if self.title_var.get().strip() else None,
            'config': config
        }
        
        # Start upload in background thread
        self.set_operation_state(True)
        threading.Thread(target=self.run_upload, args=(upload_params,), daemon=True).start()
    
    def validate_inputs(self):
        """Validate user inputs"""
        if self.tool_combobox.current() < 0:
            messagebox.showerror("선택 오류", "도구를 선택해주세요")
            return False
        
        source_path = self.source_path_var.get().strip()
        if not source_path:
            messagebox.showerror("입력 오류", "파일 또는 URL을 입력해주세요")
            return False
        
        if self.source_type_var.get() == "file" and not Path(source_path).exists():
            messagebox.showerror("파일 오류", "선택한 파일이 존재하지 않습니다")
            return False
        
        return True
    
    def detect_source_type(self):
        """Detect source type based on path"""
        if self.source_type_var.get() == "url":
            return "url"
        
        source_path = self.source_path_var.get().strip().lower()
        if source_path.endswith('.pdf'):
            return 'pdf'
        elif source_path.endswith(('.md', '.markdown')):
            return 'markdown'
        else:
            return 'text'
    
    def run_upload(self, params):
        """Run the upload process in background"""
        try:
            # Update processor config
            self.processor.config = params['config']
            
            # Run async upload
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(
                self.processor.index_document(
                    source_path=params['source_path'],
                    tool_id=params['tool_id'],
                    source_type=params['source_type'],
                    custom_title=params['custom_title']
                )
            )
            
            # Update GUI with results
            self.root.after(0, lambda: self.on_upload_complete(result))
            
        except Exception as e:
            self.root.after(0, lambda: self.on_upload_error(str(e)))
        finally:
            loop.close()
    
    def on_upload_complete(self, result):
        """Handle upload completion"""
        self.set_operation_state(False)
        
        if result['success']:
            summary = result['processing_summary']
            message = f"업로드가 완료되었습니다!\n\n"
            message += f"총 청크: {summary['total_chunks_processed']}\n"
            message += f"임베딩 생성: {summary['chunks_with_embeddings']}\n"
            message += f"저장됨: {summary['stored']}\n"
            message += f"중복 건너뜀: {summary['skipped']}"
            
            if summary['failed'] > 0:
                message += f"\n실패: {summary['failed']}"
            
            messagebox.showinfo("업로드 완료", message)
            logger.info("문서 업로드가 성공적으로 완료되었습니다")
        else:
            messagebox.showerror("업로드 실패", f"업로드 중 오류가 발생했습니다:\n{result['error']}")
            logger.error(f"문서 업로드 실패: {result['error']}")
        
        self.progress_var.set(0)
    
    def on_upload_error(self, error):
        """Handle upload error"""
        self.set_operation_state(False)
        messagebox.showerror("업로드 오류", f"업로드 중 예상치 못한 오류가 발생했습니다:\n{error}")
        logger.error(f"업로드 오류: {error}")
        self.progress_var.set(0)
    
    def show_tool_stats(self):
        """Show statistics for selected tool"""
        if self.tool_combobox.current() < 0:
            messagebox.showwarning("선택 오류", "도구를 선택해주세요")
            return
        
        tool = self.tools_data[self.tool_combobox.current()]
        
        def fetch_stats():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                result = loop.run_until_complete(
                    self.processor.get_tool_knowledge_stats(tool['id'])
                )
                
                self.root.after(0, lambda: self.display_tool_stats(result, tool['name']))
                
            except Exception as e:
                self.root.after(0, lambda: logger.error(f"통계 조회 실패: {e}"))
            finally:
                loop.close()
        
        threading.Thread(target=fetch_stats, daemon=True).start()
        self.update_status("통계 조회 중...")
    
    def display_tool_stats(self, result, tool_name):
        """Display tool statistics in a dialog"""
        if not result['success']:
            messagebox.showerror("통계 오류", f"통계 조회에 실패했습니다:\n{result['error']}")
            return
        
        # Create stats dialog
        stats_window = tk.Toplevel(self.root)
        stats_window.title(f"{tool_name} - 지식 통계")
        stats_window.geometry("600x400")
        stats_window.resizable(True, True)
        
        # Stats content
        stats_text = scrolledtext.ScrolledText(stats_window, wrap=tk.WORD)
        stats_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        content = f"🔧 도구: {tool_name}\n"
        content += f"📊 총 청크 수: {result['chunk_count']}\n\n"
        
        if result['sources']:
            content += "📁 소스별 분석:\n"
            for source in result['sources']:
                content += f"  • {source['source_title']} ({source['source_type']}) - {source['chunk_count']} 청크\n"
            content += "\n"
        
        if result['top_chunks']:
            content += "🔍 주요 콘텐츠 샘플:\n"
            for i, chunk in enumerate(result['top_chunks'][:5], 1):
                score = chunk.get('relevance_score', 'N/A')
                preview = chunk['content'][:200] + '...' if len(chunk['content']) > 200 else chunk['content']
                content += f"  {i}. [{score}] {preview}\n\n"
        
        stats_text.insert(1.0, content)
        stats_text.config(state=tk.DISABLED)
        
        self.update_status("통계 표시 완료")
    
    def cleanup_knowledge(self):
        """Clean up knowledge for selected tool"""
        if self.tool_combobox.current() < 0:
            messagebox.showwarning("선택 오류", "도구를 선택해주세요")
            return
        
        tool = self.tools_data[self.tool_combobox.current()]
        
        # Confirm cleanup
        confirm = messagebox.askyesno(
            "지식 정리 확인", 
            f"'{tool['name']}' 도구의 모든 지식을 삭제하시겠습니까?\n\n이 작업은 되돌릴 수 없습니다."
        )
        
        if not confirm:
            return
        
        def run_cleanup():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                result = loop.run_until_complete(
                    self.processor.cleanup_tool_knowledge(tool['id'])
                )
                
                self.root.after(0, lambda: self.on_cleanup_complete(result, tool['name']))
                
            except Exception as e:
                self.root.after(0, lambda: self.on_cleanup_error(str(e)))
            finally:
                loop.close()
        
        self.set_operation_state(True)
        threading.Thread(target=run_cleanup, daemon=True).start()
    
    def on_cleanup_complete(self, result, tool_name):
        """Handle cleanup completion"""
        self.set_operation_state(False)
        
        if result['success']:
            message = f"'{tool_name}' 도구의 지식 정리가 완료되었습니다.\n\n삭제된 청크: {result['deleted_count']}개"
            messagebox.showinfo("정리 완료", message)
            logger.info(f"지식 정리 완료: {result['deleted_count']}개 청크 삭제됨")
        else:
            messagebox.showerror("정리 실패", f"지식 정리 중 오류가 발생했습니다:\n{result['error']}")
            logger.error(f"지식 정리 실패: {result['error']}")
    
    def on_cleanup_error(self, error):
        """Handle cleanup error"""
        self.set_operation_state(False)
        messagebox.showerror("정리 오류", f"지식 정리 중 예상치 못한 오류가 발생했습니다:\n{error}")
        logger.error(f"정리 오류: {error}")
    
    def stop_operation(self):
        """Stop current operation"""
        # Note: This is a placeholder for operation cancellation
        # Actual implementation would need to handle async task cancellation
        messagebox.showinfo("중지", "작업 중지가 요청되었습니다.\n진행 중인 작업은 완료될 때까지 계속됩니다.")
    
    def set_operation_state(self, running: bool):
        """Set UI state for running operations"""
        if running:
            self.upload_btn.config(state=tk.DISABLED)
            self.stats_btn.config(state=tk.DISABLED)
            self.cleanup_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.progress_var.set(50)  # Indeterminate progress
        else:
            self.upload_btn.config(state=tk.NORMAL)
            self.stats_btn.config(state=tk.NORMAL)
            self.cleanup_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.progress_var.set(0)
    
    def update_status(self, message: str):
        """Update status bar message"""
        self.status_var.set(message)


def main():
    """Main function to run the GUI application"""
    # Create and run the application
    if DND_AVAILABLE:
        try:
            root = TkinterDnD.Tk()
        except:
            root = tk.Tk()
    else:
        root = tk.Tk()
    
    app = RAGUploaderGUI(root)
    
    # Handle window closing
    def on_closing():
        if messagebox.askokcancel("종료", "애플리케이션을 종료하시겠습니까?"):
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()