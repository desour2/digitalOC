'''
Currently uses a dict as input  

input dictionary:
        "yardline_100": int,
        "down": int,
        "ydstogo": int,
        "pass_length": string,
        "pass_location": string,
        "air_yards": int,
        "run_location": string,
        "run_gap": string,
        "offense_formation": string,
        "offense_personnel": string,
        "route": string,
        "involved_player_position": string

'''

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def draw_field(ax, ydstogo, yardline_100):
    ax.set_facecolor('#3A9D23')
    
    # Set field boundaries
    max_y_visible = 45 # How many yards downfield to show
    ax.set_xlim(-25, 25)  # Sideline to sideline (approx 50 yards wide)
    ax.set_ylim(-10, max_y_visible)  # 10 yards into backfield

    # Draw endzone
    if pd.notna(yardline_100) and yardline_100 < max_y_visible:
        ax.axhspan(yardline_100, max_y_visible, color='#004080', alpha=0.5)
        ax.text(-24, yardline_100 + 1, 'ENDZONE', color='white', fontsize=12, fontweight='bold')
    
    # Draw line of scrimmage
    ax.axhline(0, color='white', linestyle='--', linewidth=2, label='Line of Scrimmage')
    
    # Draw first down line
    if pd.notna(ydstogo) and ydstogo < max_y_visible:
        ax.axhline(ydstogo, color='yellow', linestyle='-', linewidth=3, label=f'1st Down ({int(ydstogo)} yds)')
    
    # Draw yard lines
    if pd.isna(yardline_100):
        for y in range(5, max_y_visible, 5):
            if (pd.notna(ydstogo) and y == ydstogo):
                continue
            ax.axhline(y, color='white', linestyle='-', alpha=0.5)
            ax.text(-24, y + 0.5, str(y), color='white', fontsize=10)
    else:
        ball_on_yardline = 100 - yardline_100
        first_marker_downfield = (ball_on_yardline // 5) * 5 + 5
        yds_to_first_marker = first_marker_downfield - ball_on_yardline
        for y_relative in range(int(yds_to_first_marker), max_y_visible, 5):
            absolute_yardline = first_marker_downfield + (y_relative - yds_to_first_marker)
            if absolute_yardline > 50:
                label = 100 - absolute_yardline
            else:
                label = absolute_yardline
            if (pd.notna(yardline_100) and y_relative == yardline_100) or \
               (pd.notna(ydstogo) and y_relative == ydstogo):
                continue
                
            ax.axhline(y_relative, color='white', linestyle='-', alpha=0.5)
            ax.text(-24, y_relative + 0.5, str(int(label)), color='white', fontsize=10)
            
    # Draw hash marks
    for y in np.arange(1, max_y_visible, 1):
        ax.plot([-9, -8], [y, y], color='white', alpha=0.5) # Left hash
        ax.plot([8, 9], [y, y], color='white', alpha=0.5)   # Right hash
        
    # Draw O-line
    ol_x = [-4, -2, 0, 2, 4]  # LT, LG, C, RG, RT
    ol_y = [0, 0, 0, 0, 0]
    ax.plot(ol_x, ol_y, 'o', color='white', markersize=10, label='Offensive Line')

    ax.set_xticks([])
    ax.set_yticks([])

def get_start_position(position, pass_location, formation):
    if position == 'RB' and 'EMPTY' in str(formation).upper():
        position = 'WR'

    if pd.isna(pass_location) or pass_location == 'middle':
        location_side = 'right'
    else:
        location_side = pass_location
        
    # Determine backfield depth based on formation
    if 'SHOTGUN' in str(formation).upper():
        backfield_y = -5
    elif 'SINGLEBACK' in str(formation).upper() or 'I_FORM' in str(formation).upper():
        backfield_y = -5 # Tailback depth for I_FORM and SINGLEBACK
    else:
        backfield_y = -5 # Default to shotgun depth

    # RB (Running Back)
    if position == 'RB':
        if 'I_FORM' in str(formation).upper() or 'SINGLEBACK' in str(formation).upper():
            return (0, backfield_y) # Tailback slot (0, -5)
        
        # Line up opposite the play direction in Shotgun
        if 'SHOTGUN' in str(formation).upper():
            if location_side == 'left':
                return (2, backfield_y) # Start offset RIGHT
            else:
                # If run is 'right' or 'middle', start offset LEFT
                return (-2, backfield_y) # Start offset LEFT

        # Starts in the backfield (Default for non-shotgun/I-form)
        if location_side == 'left':
            return (-2, backfield_y) # Offset left
        else:
            return (2, backfield_y)  # Offset right
        
    # TE (Tight End)
    elif position == 'TE':
        if location_side == 'left':
            return (-6, -0.5) # Left side
        else:
            return (6, -0.5)  # Right side
            
    # WR (Wide Receiver)
    elif position == 'WR':
        if location_side == 'left':
            return (-18, -0.5) # Wide left
        else:
            return (18, -0.5)  # Wide right
            
    # Default (if unknown position)
    else:
        return (0, 0)

def get_route_path(route_name, start_pos, position, location, air_yards):
    if pd.isna(route_name): route_name = "UNKNOWN"
    route_key = str(route_name).upper()
    
    start_x, start_y = start_pos
    is_left_side = start_x < 0
    if pd.isna(air_yards):
        if route_key == 'SCREEN': air_yards = -2 
        else: air_yards = 5 # Default 5-yard "unknown" route
    
    y = air_yards # `y` is our target depth

    if route_key == 'SCREEN' and position == 'RB':
        if location == 'left':
            relative_path = [(0, 1), (-5, y)]
        else:
            relative_path = [(0, 1), (5, y)]

    else:
        # Route definitions are now functions (lambda)
        ROUTE_DEFINITIONS = {
            'GO':       lambda y: [(0, y*0.5), (0, y)],
            'FADE':     lambda y: [(1, y*0.5), (3, y)],
            'OUT':      lambda y: [(0, y*0.8), (0, y), (5, y)], 
            'IN':       lambda y: [(0, y*0.8), (0, y), (-5, y)],
            'HITCH':    lambda y: [(0, y), (0, y-2)],
            'CURL':     lambda y: [(0, y), (0, y+2), (0, y), (-2, y)],
            'SLANT':    lambda _: [(0, 3), (-3, 6)], 
            'FLAT':     lambda _: [(3, 1), (5, 1)],
            'SCREEN':   lambda _: [(-3, 0), (-5, -2)], # WR Screen
            'WHEEL':    lambda _: [(3, 1), (5, 3), (5, 8), (3, 12), (0, 15)],
        }
        
        route_func = ROUTE_DEFINITIONS.get(route_key, lambda y: [(0, y*0.5), (1, y)]) # Default "UNKNOWN"
        relative_path = route_func(y) 

    if is_left_side and not (route_key == 'SCREEN' and position == 'RB'):
        mirror_routes = ['OUT', 'FLAT', 'IN', 'SLANT', 'FADE', 'CURL', 'SCREEN'] 
        if route_key in mirror_routes:
            relative_path = [(-x, y) for x, y in relative_path]

    absolute_path = [
        (start_x + rel_x, start_y + rel_y) 
        for rel_x, rel_y in relative_path
    ]
    
    return absolute_path

def get_run_path(run_location, run_gap, start_pos):
    target_x = 0 
    
    if run_location == 'middle':
        target_x = 0
    elif run_location == 'left':
        if run_gap == 'guard': target_x = -1
        elif run_gap == 'tackle': target_x = -3
        elif run_gap == 'end': target_x = -5
        else: target_x = -3
    elif run_location == 'right':
        if run_gap == 'guard': target_x = 1
        elif run_gap == 'tackle': target_x = 3
        elif run_gap == 'end': target_x = 5
        else: target_x = 3
            
    path_points = [
        (target_x, 0.5), # Hit the hole
        (target_x, 5)    # Run 5 yards
    ]
    return path_points

def parse_personnel(personnel_str):
    counts = {'RB': 0, 'TE': 0, 'WR': 0}
    if pd.isna(personnel_str):
        return counts
        
    personnel_str = str(personnel_str).replace('"', '')
    parts = personnel_str.split(',')
    
    for part in parts:
        part = part.strip()
        pieces = part.split(' ')
        if len(pieces) == 2:
            try:
                count = int(pieces[0])
                pos = pieces[1].strip()
                if pos in counts:
                    counts[pos] = count
            except ValueError:
                continue 
    return counts

def get_default_alignments(personnel_counts, formation, play_type='pass', location=None):
    alignments = []
    
    # Determine Backfield Depth
    if 'SHOTGUN' in str(formation).upper():
        backfield_y = -5
    elif 'SINGLEBACK' in str(formation).upper() or 'I_FORM' in str(formation).upper():
        backfield_y = -5 # Tailback depth
    else:
        backfield_y = -5 # Default

    # Define Default Slots
    WR_SLOTS = [
        (-18, -0.5), # WR 1 (Left Wide)
        (18, -0.5),  # WR 2 (Right Wide)
        (-12, -0.5), # WR 3 (Left Slot)
        (12, -0.5)   # WR 4 (Right Slot)
    ]
    
    TE_SLOT_RIGHT = (6, -0.5)
    TE_SLOT_LEFT = (-6, -0.5)
    is_run = play_type == 'run'
    run_side = str(location).lower()

    if is_run and run_side == 'left':
        TE_SLOTS = [TE_SLOT_LEFT, TE_SLOT_RIGHT]
    elif is_run and run_side == 'right':
        TE_SLOTS = [TE_SLOT_RIGHT, TE_SLOT_LEFT]
    else:
        TE_SLOTS = [TE_SLOT_RIGHT, TE_SLOT_LEFT]
        
    OFFSET_RB_SLOTS = [
        (2, backfield_y),  # RB 1 (Right Offset)
        (-2, backfield_y) # RB 2 (Left Offset)
    ]
    I_FORM_RB_SLOTS = [
        (0, -3), # FB
        (0, -5)  # TB
    ]
    
    # Fill Slots
    is_empty = 'EMPTY' in str(formation).upper()
    is_iform = 'I_FORM' in str(formation).upper()
    is_singleback = 'SINGLEBACK' in str(formation).upper()
    
    available_wr_slots = WR_SLOTS.copy()
    available_te_slots = TE_SLOTS.copy()
    
    if is_iform:
        available_rb_slots = I_FORM_RB_SLOTS.copy()
    elif is_singleback:
        available_rb_slots = [(0, backfield_y)] # Use the (0, -5) slot
    else:
        available_rb_slots = OFFSET_RB_SLOTS.copy()

    # 1. Place TEs
    for _ in range(personnel_counts.get('TE', 0)):
        if available_te_slots:
            slot = available_te_slots.pop(0) 
            alignments.append(('TE', slot))
            if slot in available_wr_slots:
                available_wr_slots.remove(slot)
                
    # 2. Place WRs
    for _ in range(personnel_counts.get('WR', 0)):
        if available_wr_slots:
            slot = available_wr_slots.pop(0)
            alignments.append(('WR', slot))
            if slot in available_te_slots:
                available_te_slots.remove(slot)

    # 3. Place RBs
    for _ in range(personnel_counts.get('RB', 0)):
        if is_empty:
            if available_wr_slots:
                slot = available_wr_slots.pop(0)
                alignments.append(('RB', slot))
            elif available_te_slots:
                slot = available_te_slots.pop(0)
                alignments.append(('RB', slot))
        else:
            if available_rb_slots:
                slot = available_rb_slots.pop(0)
                alignments.append(('RB', slot))
            else:
                alignments.append(('RB', (-2, backfield_y))) 
                
    return alignments


def visualize_play(play_data):
    """
    Accepts a dictionary 'play_data' containing all necessary play variables.
    """
    
    # Extract variables safely using .get()
    #game_id = play_data.get('game_id', 'Unknown Game')
    #play_id = play_data.get('play_id', 'Unknown Play')
    
    formation = play_data.get('offense_formation')
    personnel = play_data.get('offense_personnel')
    position = play_data.get('involved_player_position') 
    
    # Helper to safely get float/int values
    def get_num(key):
        val = play_data.get(key)
        return val if pd.notna(val) else None

    down = get_num('down')
    ydstogo = get_num('ydstogo')
    yardline_100 = get_num('yardline_100')
    
    # String formatting for display
    down_str = f"{int(down) if down else '?'} & {int(ydstogo) if ydstogo else '?'}"
    yardline_str = f"{int(yardline_100) if yardline_100 else '?'} yds to EZ"
    
    play_type = ''
    #player_name = ''
    plot_label = ''
    path_info_str = ''
    path = []
    
    # Check if it's a pass play (based on receiver presence)
    #receiver = play_data.get('receiver')
    #rusher = play_data.get('rusher')
    route  =play_data.get('route')
    run_gap = play_data.get('run_gap')
    
    if pd.notna(route):
        play_type = 'pass'
        #player_name = receiver
        route = play_data.get('route')
        location = play_data.get('pass_location') 
        air_yards = get_num('air_yards')    
        plot_label = f'Targeted Receiver ({position})'
        path_info_str = f"Route: {str(route).upper()} ({air_yards} yds)"
        
        start_pos = get_start_position(position, location, formation)
        path = get_route_path(route, start_pos, position, location, air_yards)
        
    # Check if it's a run play
    elif pd.notna(run_gap):
        play_type = 'run'
        #player_name = rusher
        location = play_data.get('run_location') 
        run_gap = play_data.get('run_gap')
        plot_label = f'Rusher ({position})'
        path_info_str = f"Run: {str(location).capitalize()} ({str(run_gap).capitalize()})"
        
        start_pos = get_start_position(position, location, formation)
        path = get_run_path(location, run_gap, start_pos)
        
    else:
        # Fallback if neither run nor pass is clear
        start_pos = (0, -1) 
        plot_label = 'Unknown Play'

    #print("\n" + "="*30)
    #print(f"{game_id} / {play_id}")
    print(f"  > Situation: {down_str} | {yardline_str}")
    print(f"  > Formation: {formation}")
    print(f"  > Personnel: {personnel}")
    print(f"  > Play Type: {play_type}")
    #print(f"  > Involved: {player_name} ({position})")
    #print("="*30 + "\n")

    fig, ax = plt.subplots(figsize=(7, 10))
    fig.patch.set_facecolor('#F0F0F0') 
    
    # Draw the field
    draw_field(ax, ydstogo, yardline_100)
    
    # Determine QB position based on formation
    formation_str = str(formation).upper()
    if 'SHOTGUN' in formation_str:
        qb_pos = (0, -5)
        qb_label = 'QB (Shotgun)'
    elif 'SINGLEBACK' in formation_str or 'I_FORM' in formation_str:
        qb_pos = (0, -1) # Under Center
        qb_label = 'QB (Under Center)'
    else:
        qb_pos = (0, -1) # Default to under center
        qb_label = 'QB (Reference)'
    
    # Plot QB
    ax.plot(qb_pos[0], qb_pos[1], 'o', color='yellow', markersize=12, label=qb_label)
    
    personnel_counts = parse_personnel(personnel)
    
    # Subtract the targeted player from the count to avoid double plotting
    if position in personnel_counts:
        personnel_counts[position] -= 1
    
    default_players = get_default_alignments(personnel_counts, formation, play_type, location)
    
    has_ghost_label = False
    for pos, (x, y) in default_players:
        if not has_ghost_label:
            ax.plot(x, y, 'o', color='white', markersize=10, alpha=0.7, label='Other Receivers')
            has_ghost_label = True
        else:
            ax.plot(x, y, 'o', color='white', markersize=10, alpha=0.7)
    
    # Plot the targeted player (Rusher or Receiver)
    start_x, start_y = start_pos
    ax.plot(start_x, start_y, 'o', color='cyan', markersize=12, label=plot_label)

    # Plot the Path (Route or Run)
    if path:
        full_path_x = [start_x] + [x for x, y in path]
        full_path_y = [start_y] + [y for x, y in path]
        
        ax.plot(full_path_x, full_path_y, '-', color='cyan', linewidth=3)
        
        ax.arrow(full_path_x[-2], full_path_y[-2], 
                 full_path_x[-1] - full_path_x[-2], 
                 full_path_y[-1] - full_path_y[-2],
                 head_width=1, head_length=1, fc='cyan', ec='cyan', length_includes_head=True)

    title_text = (
        #f"Game: {game_id} | Play: {play_id}\n"
        f"{down_str} | {yardline_str}\n" 
        #f"Player: {player_name}\n"
        f"Position: {position} | {path_info_str}\n" 
        f"Formation: {formation} | Personnel: {personnel}"
    )
    ax.set_title(title_text, fontsize=12)
    
    # Re-order the legend
    handles, labels = ax.get_legend_handles_labels()
    unique_labels = {}
    for h, l in zip(handles, labels):
        if l not in unique_labels:
            unique_labels[l] = h
            
    handles = unique_labels.values()
    labels = unique_labels.keys()
    
    ax.legend(handles=handles, labels=labels, loc='lower left')
    
    plt.show()

if __name__ == "__main__":

# test pass play
    pass_play_input = {
        "yardline_100": 25,
        "down": 1,
        "ydstogo": 10,
        "pass_length": "short",
        "pass_location": "left",
        "air_yards": 8,
        "run_location": None,
        "run_gap": None,
        "rusher": None,
        "receiver": "D.Hopkins",
        "offense_formation": "SHOTGUN",
        "offense_personnel": "1 RB, 1 TE, 3 WR",
        "route": "IN",
        "involved_player_position": "WR"
    }

# test run play
    run_play_input = {
        "yardline_100": 40,
        "down": 2,
        "ydstogo": 6,
        "pass_length": None,
        "pass_location": None,
        "air_yards": None,
        "run_location": "right",
        "run_gap": "tackle",
        "rusher": "D.Cook",
        "receiver": None,
        "offense_formation": "I_FORM",
        "offense_personnel": "2 RB, 2 TE, 1 WR",
        "route": None,
        "involved_player_position": "RB"
    }

    visualize_play(pass_play_input)
