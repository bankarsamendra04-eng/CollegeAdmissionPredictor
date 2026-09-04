import os
import random
import csv

os.makedirs('data', exist_ok=True)

# 1. Colleges
colleges = [
    ("Government College of Engineering Pune", "Pune", "Pune", "Government", "Savitribai Phule Pune University"),
    ("VJTI Mumbai", "Mumbai", "Mumbai City", "Government-Aided", "Mumbai University"),
    ("COEP Technological University", "Pune", "Pune", "Autonomous", "COEP Technological University"),
    ("Walchand College of Engineering", "Sangli", "Sangli", "Government-Aided", "Shivaji University"),
    ("Sardar Patel Institute of Technology", "Mumbai", "Mumbai Suburban", "Autonomous", "Mumbai University"),
    ("Pune Institute of Computer Technology", "Pune", "Pune", "Private", "Savitribai Phule Pune University"),
    ("Dwarkadas J. Sanghvi College of Engineering", "Mumbai", "Mumbai Suburban", "Private", "Mumbai University"),
    ("Vishwakarma Institute of Technology", "Pune", "Pune", "Autonomous", "Savitribai Phule Pune University"),
    ("KJ Somaiya College of Engineering", "Mumbai", "Mumbai Suburban", "Autonomous", "Somaiya Vidyavihar University"),
    ("Thadomal Shahani Engineering College", "Mumbai", "Mumbai Suburban", "Private", "Mumbai University"),
    ("Government College of Engineering Aurangabad", "Aurangabad", "Aurangabad", "Government", "Dr. Babasaheb Ambedkar Marathwada University"),
    ("Government College of Engineering Amravati", "Amravati", "Amravati", "Government", "Sant Gadge Baba Amravati University"),
    ("Shri Ramdeobaba College of Engineering and Management", "Nagpur", "Nagpur", "Autonomous", "Rashtrasant Tukadoji Maharaj Nagpur University"),
    ("Pimpri Chinchwad College of Engineering", "Pune", "Pune", "Private", "Savitribai Phule Pune University"),
    ("Fr. Conceicao Rodrigues College of Engineering", "Mumbai", "Mumbai Suburban", "Private", "Mumbai University"),
    ("Cummins College of Engineering for Women", "Pune", "Pune", "Autonomous", "Savitribai Phule Pune University"),
    ("Bansilal Ramnath Agarwal Charitable Trust's Vishwakarma Institute of Information Technology", "Pune", "Pune", "Autonomous", "Savitribai Phule Pune University"),
    ("Yeshwantrao Chavan College of Engineering", "Nagpur", "Nagpur", "Autonomous", "Rashtrasant Tukadoji Maharaj Nagpur University"),
    ("Thakur College of Engineering and Technology", "Mumbai", "Mumbai Suburban", "Autonomous", "Mumbai University"),
    ("Rajiv Gandhi Institute of Technology", "Mumbai", "Mumbai Suburban", "Private", "Mumbai University"),
    ("Vidyalankar Institute of Technology", "Mumbai", "Mumbai City", "Private", "Mumbai University"),
    ("MIT World Peace University", "Pune", "Pune", "Private", "MIT-WPU"),
    ("Symbiosis Institute of Technology", "Pune", "Pune", "Private", "Symbiosis International University"),
    ("G. H. Raisoni College of Engineering", "Nagpur", "Nagpur", "Autonomous", "Rashtrasant Tukadoji Maharaj Nagpur University"),
    ("DKTE Society's Textile and Engineering Institute", "Ichalkaranji", "Kolhapur", "Autonomous", "Shivaji University"),
    ("Government College of Engineering Karad", "Karad", "Satara", "Government", "Shivaji University"),
    ("Rajarambapu Institute of Technology", "Islampur", "Sangli", "Autonomous", "Shivaji University"),
    ("K. K. Wagh Institute of Engineering Education & Research", "Nashik", "Nashik", "Autonomous", "Savitribai Phule Pune University"),
    ("Sanjeevan Engineering and Technology Institute", "Panhala", "Kolhapur", "Private", "Shivaji University"),
    ("Sanjivani Rural Education Society's College of Engineering", "Kopargaon", "Ahmednagar", "Autonomous", "Savitribai Phule Pune University"),
    ("Government College of Engineering Jalgaon", "Jalgaon", "Jalgaon", "Government", "Kavayitri Bahinabai Chaudhari North Maharashtra University"),
    ("Government College of Engineering Nagpur", "Nagpur", "Nagpur", "Government", "Rashtrasant Tukadoji Maharaj Nagpur University"),
    ("Government College of Engineering Chandrapur", "Chandrapur", "Chandrapur", "Government", "Gondwana University"),
    ("Usha Mittal Institute of Technology", "Mumbai", "Mumbai Suburban", "University Department", "SNDT Women's University"),
    ("Institute of Chemical Technology", "Mumbai", "Mumbai City", "Autonomous", "Institute of Chemical Technology")
]

with open('data/colleges.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['id','name','city','district','state','college_type','university','fees_per_year','avg_package_lpa','highest_package_lpa','accreditation','established_year','naac_grade','nba_accredited','total_seats'])
    f.write('# DEMO DATA - Sample dataset for demonstration purposes only\n')
    for i, c in enumerate(colleges):
        c_id = i + 1
        name, city, district, ctype, uni = c
        fees = random.randint(30000, 80000) if 'Government' in ctype else random.randint(80000, 200000)
        avg_pkg = round(random.uniform(4.0, 15.0) if 'Government' not in ctype else random.uniform(5.0, 20.0), 1)
        highest_pkg = round(random.uniform(10.0, 80.0), 1)
        est_year = random.randint(1950, 2010)
        naac = random.choice(['A++', 'A+', 'A', 'B++', 'B+', 'B', 'C'])
        nba = random.choice(['Yes', 'No'])
        total_seats = random.randint(300, 1200)
        writer.writerow([c_id, name, city, district, "Maharashtra", ctype, uni, fees, avg_pkg, highest_pkg, "AICTE", est_year, naac, nba, total_seats])

# 2. Branches
branches = [
    ("Computer Science and Engineering", "CSE"),
    ("Information Technology", "IT"),
    ("Artificial Intelligence and Machine Learning", "AIML"),
    ("Artificial Intelligence and Data Science", "AIDS"),
    ("Data Science", "DS"),
    ("Electronics and Telecommunication Engg", "EXTC"),
    ("Electronics Engineering", "ELEX"),
    ("Electrical Engineering", "EE"),
    ("Mechanical Engineering", "MECH"),
    ("Civil Engineering", "CIVIL")
]

branch_data = []
with open('data/branches.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['id','college_id','branch_name','branch_code','total_seats','open_seats','obc_seats','sc_seats','st_seats','ews_seats','vjdt_seats','nt_seats','sbc_seats'])
    b_id = 1
    for c_id in range(1, 36):
        num_branches = random.randint(3, 8)
        selected_branches = random.sample(branches, num_branches)
        for b_name, b_code in selected_branches:
            total = random.choice([60, 120])
            open_s = int(total * 0.5)
            obc_s = int(total * 0.19)
            sc_s = int(total * 0.13)
            st_s = int(total * 0.07)
            ews_s = int(total * 0.1)
            vjdt_s = int(total * 0.01)
            nt_s = int(total * 0.01)
            sbc_s = total - (open_s + obc_s + sc_s + st_s + ews_s + vjdt_s + nt_s)
            
            writer.writerow([b_id, c_id, b_name, b_code, total, open_s, obc_s, sc_s, st_s, ews_s, vjdt_s, nt_s, sbc_s])
            branch_data.append((b_id, c_id, b_name))
            b_id += 1

# 3. Cutoffs
categories = ['OPEN', 'OBC', 'SC', 'ST', 'EWS', 'VJ', 'NTA', 'NTB', 'NTC', 'NTD', 'SBC']
genders = ['ALL', 'FEMALE']
years = [2022, 2023, 2024]
rounds = [1, 2, 3]

with open('data/cutoffs.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['id','college_id','branch_id','year','category','gender','round','opening_rank','closing_rank'])
    c_id_seq = 1
    for b_id, c_id, b_name in branch_data:
        base_rank = random.randint(100, 50000)
        for year in years:
            for cat in categories:
                for gen in genders:
                    for rnd in rounds:
                        # random fluctuations
                        factor = 1.0 + (rnd - 1) * 0.1
                        if cat != 'OPEN':
                            factor *= random.uniform(1.2, 2.5)
                        if gen == 'FEMALE':
                            factor *= 1.1
                        if year == 2023:
                            factor *= 0.95
                        elif year == 2024:
                            factor *= 0.9
                            
                        open_r = int(base_rank * factor * random.uniform(0.7, 0.9))
                        close_r = int(base_rank * factor * random.uniform(1.1, 1.5))
                        open_r = max(1, open_r)
                        close_r = max(open_r + 1, close_r)
                        
                        writer.writerow([c_id_seq, c_id, b_id, year, cat, gen, rnd, open_r, close_r])
                        c_id_seq += 1

# 4. Placements
with open('data/placements.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['id','college_id','year','companies_visited','students_placed','placement_percentage','avg_package_lpa','median_package_lpa','highest_package_lpa'])
    p_id = 1
    for c_id in range(1, 36):
        for year in years:
            comp = random.randint(20, 150)
            placed = random.randint(100, 800)
            perc = random.uniform(60.0, 99.0)
            avg_p = random.uniform(4.0, 15.0)
            med_p = avg_p * random.uniform(0.8, 1.0)
            high_p = avg_p * random.uniform(2.0, 5.0)
            
            writer.writerow([p_id, c_id, year, comp, placed, round(perc, 1), round(avg_p, 1), round(med_p, 1), round(high_p, 1)])
            p_id += 1
