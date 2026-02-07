import streamlit as st

def render_header(athlete_name: str = "Demo Runner"):
    """
    Renders the new 4.1 Header with HTML/Tailwind.
    """
    st.markdown(f"""
    <header class="bg-white/80 dark:bg-surface-dark/90 backdrop-blur-md sticky top-0 z-50 border-b border-gray-200 dark:border-gray-800 shadow-sm mb-4">
        <div class="container mx-auto px-4 py-1">
            <div class="flex items-center justify-between gap-2">
                <!-- LOGO -->
                <div class="flex-shrink-0 flex items-center gap-2">
                    <div>
                        <div class="text-xl font-extrabold tracking-tight leading-none">
                            <span class="text-[#FF6B6B]">s</span><span class="text-[#5CB338]">C</span><span class="text-[#FFC145]">o</span><span class="text-[#FF6B6B]">re</span>
                        </div>
                        <div class="text-[0.5rem] text-gray-500 dark:text-gray-400 tracking-widest uppercase">Corri. Analizza. Evolvi</div>
                    </div>
                </div>

                <!-- RIGHT SIDE -->
                <div class="flex items-center gap-1.5 flex-shrink-0">
                    <!-- DESKTOP NAV -->
                    <nav class="hidden lg:flex items-center gap-1 mr-1">
                        <a class="flex items-center gap-0.5 px-1.5 py-0.5 rounded-lg text-[11px] font-medium text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-primary transition-all whitespace-nowrap group" href="#">
                            <span class="material-icons-round text-blue-400 group-hover:text-primary transition-colors text-sm">analytics</span>
                            Breakdown
                        </a>
                        <a class="flex items-center gap-0.5 px-1.5 py-0.5 rounded-lg text-[11px] font-medium text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-primary transition-all whitespace-nowrap group" href="#">
                            <span class="material-icons-round text-yellow-500 group-hover:text-primary transition-colors text-sm">emoji_events</span>
                            Awards
                        </a>
                        <a class="flex items-center gap-0.5 px-1.5 py-0.5 rounded-lg text-[11px] font-medium text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-primary transition-all whitespace-nowrap group" href="#">
                            <span class="material-icons-round text-purple-400 group-hover:text-primary transition-colors text-sm">bug_report</span>
                            Bug/Idea
                        </a>
                    </nav>

                    <div class="h-5 w-px bg-gray-200 dark:bg-gray-700 mx-0.5 hidden lg:block"></div>

                    <!-- USER PROFILE -->
                    <div class="flex items-center gap-1.5">
                        <div class="h-7 w-7 rounded-full bg-gray-200 dark:bg-gray-700 overflow-hidden shadow-sm ring-1 ring-white dark:ring-gray-600">
                             <!-- Fallback Avatar or Real Image -->
                             <span class="flex h-full w-full items-center justify-center text-[10px]">👤</span>
                        </div>
                        <div class="hidden md:flex flex-col">
                            <span class="text-[10px] font-bold text-gray-800 dark:text-white leading-tight">{athlete_name}</span>
                            <span class="text-[8px] text-gray-500 dark:text-gray-400 leading-tight">Premium Member</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- MOBILE NAV (Optional/Hidden for now to save space or implement later) -->
        </div>
    </header>
    """, unsafe_allow_html=True)
