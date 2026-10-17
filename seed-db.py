"""
seed-db.py — Creates and seeds productdb.db with:
  • Full schema (7 tables)
  • 500 realistic fashion & accessories products
  • 1 demo user with pre-filled basket, wishlist, and reviews

Run:  python seed-db.py
"""

import sqlite3, os, random
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), 'productdb.db')

if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
    print("Removed existing database.")

con = sqlite3.connect(DB_PATH)
cur = con.cursor()

# ── Schema ───────────────────────────────────────────────────────────
cur.executescript("""
    PRAGMA foreign_keys = ON;

    CREATE TABLE Users (
        user_id  INTEGER  PRIMARY KEY AUTOINCREMENT,
        username TEXT     NOT NULL UNIQUE,
        password TEXT     NOT NULL,
        email    TEXT     NOT NULL UNIQUE
    );

    CREATE TABLE products (
        id          INTEGER  PRIMARY KEY AUTOINCREMENT,
        name        TEXT     NOT NULL,
        description TEXT     NOT NULL,
        price       REAL     NOT NULL,
        image_url   TEXT
    );

    CREATE TABLE review (
        review_id   INTEGER  PRIMARY KEY AUTOINCREMENT,
        user_id     INTEGER  NOT NULL,
        product_id  INTEGER  NOT NULL,
        name        TEXT     NOT NULL,
        description TEXT     NOT NULL,
        created_at  DATETIME DEFAULT (datetime('now')),
        FOREIGN KEY (user_id)    REFERENCES Users(user_id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    );

    CREATE TABLE Basket (
        basket_id  INTEGER  PRIMARY KEY AUTOINCREMENT,
        user_id    INTEGER  NOT NULL,
        product_id INTEGER  NOT NULL,
        quantity   INTEGER  NOT NULL DEFAULT 1,
        added_at   DATETIME DEFAULT (datetime('now')),
        FOREIGN KEY (user_id)    REFERENCES Users(user_id),
        FOREIGN KEY (product_id) REFERENCES products(id),
        UNIQUE (user_id, product_id)
    );

    CREATE TABLE Favorites (
        user_id    INTEGER  NOT NULL,
        product_id INTEGER  NOT NULL,
        added_at   DATETIME DEFAULT (datetime('now')),
        PRIMARY KEY (user_id, product_id),
        FOREIGN KEY (user_id)    REFERENCES Users(user_id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    );

    CREATE TABLE Orders (
        order_id         INTEGER  PRIMARY KEY AUTOINCREMENT,
        user_id          INTEGER  NOT NULL,
        order_date       DATETIME DEFAULT (datetime('now')),
        total            REAL     NOT NULL,
        status           TEXT     NOT NULL DEFAULT 'pending',
        stripe_intent_id TEXT,
        order_ref        TEXT     UNIQUE,
        FOREIGN KEY (user_id) REFERENCES Users(user_id)
    );

    CREATE TABLE OrderDetails (
        order_details_id       INTEGER  PRIMARY KEY AUTOINCREMENT,
        order_id               INTEGER  NOT NULL,
        product_id             INTEGER  NOT NULL,
        quantity               INTEGER  NOT NULL,
        price_at_time_of_order REAL     NOT NULL,
        FOREIGN KEY (order_id)   REFERENCES Orders(order_id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    );
""")
print("Schema created.")

# ── Product catalogue — 500 items ────────────────────────────────────
# Images re-use real Pexels fashion URLs so every card has a real photo

IMG = {
    "shirt_white":  "https://images.pexels.com/photos/3765976/pexels-photo-3765976.jpeg?auto=compress&cs=tinysrgb&w=800",
    "shirt_black":  "https://images.pexels.com/photos/3586020/pexels-photo-3586020.jpeg?auto=compress&cs=tinysrgb&w=800",
    "earring_w":    "https://images.pexels.com/photos/9969730/pexels-photo-9969730.jpeg?auto=compress&cs=tinysrgb&w=800",
    "outfit_pink":  "https://images.pexels.com/photos/19881397/pexels-photo-19881397/free-photo-of-woman-posing-in-pink-outfit.jpeg?auto=compress&cs=tinysrgb&w=800",
    "earring_pearl":"https://images.pexels.com/photos/9428779/pexels-photo-9428779.jpeg?auto=compress&cs=tinysrgb&w=800",
    "earring_gem":  "https://images.pexels.com/photos/17298631/pexels-photo-17298631/free-photo-of-earring-with-diamonds-and-emeralds.jpeg?auto=compress&cs=tinysrgb&w=800",
    "blouse":       "https://images.pexels.com/photos/1462637/pexels-photo-1462637.jpeg?auto=compress&cs=tinysrgb&w=800",
    "dress_floral": "https://images.pexels.com/photos/1536619/pexels-photo-1536619.jpeg?auto=compress&cs=tinysrgb&w=800",
    "dress_midi":   "https://images.pexels.com/photos/1021693/pexels-photo-1021693.jpeg?auto=compress&cs=tinysrgb&w=800",
    "dress_wrap":   "https://images.pexels.com/photos/985635/pexels-photo-985635.jpeg?auto=compress&cs=tinysrgb&w=800",
    "jeans":        "https://images.pexels.com/photos/1082529/pexels-photo-1082529.jpeg?auto=compress&cs=tinysrgb&w=800",
    "trousers":     "https://images.pexels.com/photos/4498155/pexels-photo-4498155.jpeg?auto=compress&cs=tinysrgb&w=800",
    "coat":         "https://images.pexels.com/photos/1620760/pexels-photo-1620760.jpeg?auto=compress&cs=tinysrgb&w=800",
    "shoes_heels":  "https://images.pexels.com/photos/1148957/pexels-photo-1148957.jpeg?auto=compress&cs=tinysrgb&w=800",
    "shoes_trainers":"https://images.pexels.com/photos/1598505/pexels-photo-1598505.jpeg?auto=compress&cs=tinysrgb&w=800",
    "bag_shoulder": "https://images.pexels.com/photos/1152077/pexels-photo-1152077.jpeg?auto=compress&cs=tinysrgb&w=800",
    "bag_tote":     "https://images.pexels.com/photos/934063/pexels-photo-934063.jpeg?auto=compress&cs=tinysrgb&w=800",
    "scarf":        "https://images.pexels.com/photos/3622608/pexels-photo-3622608.jpeg?auto=compress&cs=tinysrgb&w=800",
    "hat":          "https://images.pexels.com/photos/1183266/pexels-photo-1183266.jpeg?auto=compress&cs=tinysrgb&w=800",
    "activewear":   "https://images.pexels.com/photos/6311387/pexels-photo-6311387.jpeg?auto=compress&cs=tinysrgb&w=800",
    "lounge":       "https://images.pexels.com/photos/4498155/pexels-photo-4498155.jpeg?auto=compress&cs=tinysrgb&w=800",
    "graphic_tee":  "https://images.pexels.com/photos/2294342/pexels-photo-2294342.jpeg?auto=compress&cs=tinysrgb&w=800",
    "linen_shirt":  "https://images.pexels.com/photos/297933/pexels-photo-297933.jpeg?auto=compress&cs=tinysrgb&w=800",
    "hoodie":       "https://images.pexels.com/photos/6311387/pexels-photo-6311387.jpeg?auto=compress&cs=tinysrgb&w=800",
}

products = [
    # ── TOPS (60) ──────────────────────────────────────────────────────
    ("Classic White Oxford Shirt", "A wardrobe cornerstone. Crisp 100% cotton Oxford weave with a semi-spread collar. Pairs perfectly with tailored trousers or denim.", 34.99, IMG["shirt_white"]),
    ("Black Slim-Fit Shirt", "Sleek and versatile. This slim-cut black shirt in breathable poplin is your go-to for smart-casual dressing, day or night.", 29.99, IMG["shirt_black"]),
    ("Striped Breton Top", "A French coastal classic. Navy and white horizontal stripes in soft jersey. Effortlessly chic with rolled-up jeans.", 24.99, IMG["shirt_white"]),
    ("Oversized Graphic Tee", "Relaxed and expressive. A heavyweight cotton tee with a vintage-inspired graphic print. Gets better with every wash.", 19.99, IMG["graphic_tee"]),
    ("Silk Blouse — Ivory", "Luxurious 100% mulberry silk blouse with a relaxed fit and delicate button-through front. Drapes beautifully at every angle.", 89.99, IMG["blouse"]),
    ("Linen Shirt — Sky Blue", "Summer-ready linen in a breezy sky-blue colourway. Slightly relaxed fit with wooden buttons. Machine washable.", 39.99, IMG["linen_shirt"]),
    ("Off-Shoulder Ruffle Top", "Romantic and feminine. A soft woven top with an elasticated off-shoulder neckline and layered ruffle detailing.", 32.99, IMG["dress_floral"]),
    ("Ribbed Crop Top — White", "Minimal and modern. A ribbed stretch-cotton crop top that sits just above the waist. Pairs with everything.", 16.99, IMG["activewear"]),
    ("Floral Wrap Blouse", "A garden-fresh print on flowing viscose. The adjustable wrap front flatters every shape and ties neatly at the waist.", 44.99, IMG["blouse"]),
    ("Boucle Collarless Jacket Top", "Textured boucle in warm cream. This collarless jacket-top hybrid sits at the hip and elevates any outfit instantly.", 74.99, IMG["shirt_white"]),
    ("Oversized Tee — Sage Green", "Sage green heavy-weight cotton. Cut longer at the back for a contemporary street-style silhouette.", 22.99, IMG["graphic_tee"]),
    ("Puff-Sleeve Blouse — Blush", "Romantic puff sleeves in soft blush crepe. Button-up front with a V-neckline that is flattering and feminine.", 48.99, IMG["blouse"]),
    ("Fitted Polo Shirt — Navy", "A preppy classic reinvented. Pique cotton polo with a slim, contemporary fit and contrast tipping on the collar.", 27.99, IMG["shirt_black"]),
    ("Tie-Front Crop Shirt", "Take the classic shirt and give it a twist. Knot it at the waist for a 70s-inspired look over high-waisted trousers.", 36.99, IMG["linen_shirt"]),
    ("Sheer Organza Blouse — Black", "Lightweight organza with a subtle shimmer. Layer over a cami for evening wear or a bralette for a bold daytime look.", 54.99, IMG["blouse"]),
    ("Slogan Print Tee — Black", "Soft ring-spun cotton with a bold typographic slogan print. Relaxed fit, ribbed crew neck, unisex sizing available.", 18.99, IMG["graphic_tee"]),
    ("Broderie Anglaise Blouse", "Intricate broderie anglaise embroidery on crisp white cotton. A peasant-inspired neckline makes this instantly summery.", 42.99, IMG["blouse"]),
    ("Longline Satin Camisole — Champagne", "An elevated evening essential. Adjustable spaghetti straps, bias-cut satin, and a delicate lace trim at the hem.", 38.99, IMG["dress_floral"]),
    ("Utility Overshirt — Khaki", "Washed cotton utility shirt with patch pockets and an easy, layerable fit. Wear open over a tee or buttoned as a top.", 49.99, IMG["linen_shirt"]),
    ("Denim Western Shirt", "A classic western-inspired denim shirt with snap-button closure and embroidered yoke detailing at the back.", 52.99, IMG["shirt_black"]),
    ("Ribbed Turtleneck — Camel", "A fine-gauge ribbed turtleneck in a warm camel tone. Slim fit, long sleeves, and an endlessly versatile colourway.", 44.99, IMG["shirt_white"]),
    ("Pintuck Detail Blouse — White", "Delicate pintuck pleating adds texture to this simple white blouse. Button-back, relaxed fit, and lightweight fabric.", 46.99, IMG["blouse"]),
    ("Asymmetric Hem Top — Terracotta", "A bold asymmetric hem in earthy terracotta. The draped silhouette is flattering and movement-friendly.", 39.99, IMG["dress_floral"]),
    ("Velvet Cami — Emerald", "Rich emerald velvet with delicate adjustable straps. A luxurious evening layer or statement standalone top.", 58.99, IMG["dress_wrap"]),
    ("Cropped Leather Biker Top", "Mini-cropped leather-look biker top with zip detailing on the sleeves. The edgiest piece in any wardrobe.", 79.99, IMG["shirt_black"]),
    ("Embroidered Peasant Blouse", "A boho-inspired peasant blouse with intricate floral embroidery across the chest. Square neckline and billowing sleeves.", 55.99, IMG["blouse"]),
    ("Longline Stripe Shirt — Red/White", "Classic vertical stripes in bold red and white on a longer shirt silhouette. Wear tucked in or breezy and loose.", 34.99, IMG["linen_shirt"]),
    ("Ruched Bodysuit — Black", "Flattering ruched detail across the torso in a sleek black bodysuit. Thong back for a seamless finish.", 32.99, IMG["activewear"]),
    ("Crew Neck Sweatshirt — Ecru", "Heavyweight French terry sweatshirt in clean ecru. Embroidered logo at chest. A modern classic.", 54.99, IMG["hoodie"]),
    ("Floral Embroidered Shirt", "A bold floral embroidery pattern blooms across this relaxed-fit shirt. 100% cotton, ideal for warm-weather dressing.", 48.99, IMG["linen_shirt"]),
    ("Tie-Dye Relaxed Tee", "Hand-dyed tie-dye patterns on organic cotton. Every piece is unique. Boxy fit, dropped shoulders.", 26.99, IMG["graphic_tee"]),
    ("Cold-Shoulder Top — Dusty Rose", "A cold-shoulder cutout adds drama to this dusty-rose jersey top. Flowy and comfortable for all-day wear.", 28.99, IMG["blouse"]),
    ("Wrap-Front Blouse — Burgundy", "A deep burgundy wrap-front blouse with a flattering V-neckline and long cuffed sleeves. Perfect for the office.", 52.99, IMG["blouse"]),
    ("Sheer Print Blouse — Abstract", "An abstract print on sheer georgette. Bold and wearable — layer over a slip or cami.", 44.99, IMG["dress_wrap"]),
    ("Cotton Poplin Shirt — Pale Yellow", "A pop of sunshine in premium cotton poplin. Classic collar, button-through, and a gently relaxed fit.", 36.99, IMG["linen_shirt"]),
    ("One-Shoulder Top — White", "A single sculptural shoulder in stretch jersey. Clean and contemporary — no jewellery required.", 37.99, IMG["dress_floral"]),
    ("Smocked Puff Sleeve Blouse", "Romantic smocking across the chest paired with voluminous puff sleeves. In a soft cotton lawn fabric.", 43.99, IMG["blouse"]),
    ("Fitted Ribbed Longsleeve — Black", "A second-skin ribbed longsleeve that goes under everything or stands alone. Essential layering piece.", 19.99, IMG["activewear"]),
    ("Cropped Hoodie — Lavender", "A soft brushed-fleece cropped hoodie in a dreamy lavender tone. Relaxed kangaroo pocket, adjustable drawstring.", 42.99, IMG["hoodie"]),
    ("Halter Neck Tie-Top — Cream", "A minimalist halter-neck that ties at the nape. In breathable crinkle cotton — perfect for holiday dressing.", 24.99, IMG["dress_floral"]),
    ("Satin Blouse — Cobalt Blue", "Rich cobalt satin with a subtle sheen. Loose fit with a statement oversized collar. The definition of dressed-up.", 67.99, IMG["blouse"]),
    ("Longline Tank — Charcoal", "A longline cotton tank in deep charcoal. Perfect as a layering base or a standalone summer top.", 14.99, IMG["shirt_black"]),
    ("Zip-Up Polo — Forest Green", "A modern polo reimagined with a zip-up neck and subtle ribbing. Wearable as a lightweight midlayer.", 34.99, IMG["linen_shirt"]),
    ("Draped Cowl-Neck Top — Stone", "A beautifully draped cowl neckline in fluid stone-coloured jersey. Moves with the body and requires zero effort.", 46.99, IMG["dress_wrap"]),
    ("Printed Kimono Blouse", "A flowing kimono-style blouse with a bold oriental-inspired print. Waterfall front opens elegantly.", 56.99, IMG["blouse"]),
    ("Thermal Henley — Oatmeal", "A waffle-knit thermal Henley in warm oatmeal. Three-button placket and a slim, flattering silhouette.", 31.99, IMG["shirt_white"]),
    ("Scoop-Neck Jersey Top — White", "The purest basic: a soft jersey scoop-neck top in brilliant white. Goes under, over, and with everything.", 12.99, IMG["shirt_white"]),
    ("Sequin Embellished Top — Gold", "All-over gold sequin top for maximum impact. Loose and lightweight — more comfortable than it looks.", 64.99, IMG["dress_floral"]),
    ("Plaid Flannel Shirt — Red/Black", "A bold red-and-black plaid check in soft flannel. A heritage pattern with a contemporary relaxed cut.", 44.99, IMG["shirt_black"]),
    ("Oversized Longline Blazer-Shirt", "The blazer and shirt had a very stylish baby. Structured shoulders, patch pockets, and an oversized, powerful silhouette.", 82.99, IMG["coat"]),
    ("Linen Shirt Dress — Ecru", "A longline linen top that doubles as a mini shirt-dress. Belted or left loose, it always looks considered.", 49.99, IMG["linen_shirt"]),
    ("Abstract Print Wrap Top", "A bold abstract print on a wrap-front top in lightweight georgette. Tie-waist, V-neckline, and endless versatility.", 42.99, IMG["blouse"]),
    ("Twist-Front Jersey Top — Olive", "A twist-front jersey top in deep olive. The knot detail creates a flattering shape at the waist.", 26.99, IMG["shirt_white"]),
    ("Lace-Trim Cami — Sage", "A delicate lace-trim cami in sage green. Satin-effect fabric, adjustable straps, barely-there finish.", 28.99, IMG["dress_floral"]),
    ("Ruched Crop Hoodie — Lilac", "A ruched crop hoodie in pastel lilac. Drawstring hood, kangaroo pocket, and a flattering cropped length.", 38.99, IMG["hoodie"]),
    ("Half-Zip Sweatshirt — Dusty Pink", "A relaxed half-zip sweatshirt in dusty pink fleece. An elevated take on the classic casual top.", 48.99, IMG["hoodie"]),
    ("Longline Cardigan — Ecru", "A longline open-front cardigan in soft ecru. Cosy enough for autumn, lightweight enough for spring.", 62.99, IMG["shirt_white"]),
    ("High-Neck Knit Dress Top — Cream", "A slim high-neck knitted top in cream. Long sleeves and a clean silhouette — layering or statement.", 46.99, IMG["shirt_white"]),
    ("Velvet Zip Hoodie — Black", "A plush velvet zip-up hoodie in jet black. Velour interior, smooth velvet exterior, ribbed cuffs.", 68.99, IMG["hoodie"]),
    ("Padded Shoulder Blouse — Cream", "Strong shoulders in cream satin. Structured pads give this blouse a powerful, editorial silhouette.", 59.99, IMG["blouse"]),

    # ── BOTTOMS (60) ───────────────────────────────────────────────────
    ("High-Waist Straight Jeans — Blue", "The perfect everyday jean. High-waisted, straight-leg fit in classic mid-blue with a slight stretch for comfort.", 59.99, IMG["jeans"]),
    ("Wide-Leg Trousers — Cream", "Flowing wide-leg trousers in a creamy hessian-weave fabric. High-waisted with a slightly pleated front.", 64.99, IMG["trousers"]),
    ("Mini Skirt — Denim", "A wardrobe classic. Straight-cut denim mini with a button-through front and raw-hem finish.", 39.99, IMG["jeans"]),
    ("Pleated Midi Skirt — Sage", "Weightless pleated chiffon in a muted sage green. Falls to mid-calf with a flattering A-line silhouette.", 54.99, IMG["trousers"]),
    ("Cargo Trousers — Khaki", "Relaxed utility cargo pants with oversized patch pockets and an adjustable waistband. Comfort meets function.", 49.99, IMG["trousers"]),
    ("Pencil Skirt — Black", "A power-dressing essential. A tailored pencil skirt in stretch ponte. Flattering, figure-hugging, professional.", 44.99, IMG["jeans"]),
    ("Paperbag Waist Trousers — Rust", "A gathered paperbag waistline in warm rust-coloured linen. Relaxed fit through the leg with tapered ankles.", 57.99, IMG["trousers"]),
    ("Faux-Leather Leggings — Black", "Sleek faux-leather leggings with a pull-on waistband. A high-shine finish that looks expensive.", 38.99, IMG["jeans"]),
    ("Tiered Maxi Skirt — Floral", "A festival-ready tiered maxi skirt in a vibrant floral print. Elastic waist, fully lined, beautifully voluminous.", 62.99, IMG["trousers"]),
    ("Tailored Shorts — Navy", "Smart tailored shorts in a smooth navy fabric. High-rise fit with belt loops and a concealed zip-fly.", 34.99, IMG["jeans"]),
    ("Satin Bias-Cut Skirt — Champagne", "A slinky bias-cut satin skirt that skims the body. Champagne colourway with a concealed side zip.", 68.99, IMG["trousers"]),
    ("Slim-Fit Chinos — Stone", "Tailored chinos in a classic stone colourway. Slim through the hip and thigh, tapered at the ankle.", 47.99, IMG["jeans"]),
    ("Ruched Mini Skirt — Red", "A bodycon ruched mini in stretch fabric. Side ruching creates a gathered effect that flatters the figure.", 29.99, IMG["jeans"]),
    ("Linen Wide-Leg Shorts — White", "Breathable linen shorts cut with a relaxed wide-leg silhouette. Elastic back waist for easy fit.", 32.99, IMG["trousers"]),
    ("Skinny Jeans — Black", "A go-to skinny jean in stretch black denim. High-rise waist, smooth through the hip, skinny from thigh to ankle.", 52.99, IMG["jeans"]),
    ("Palazzo Trousers — Leopard Print", "Bold animal print on a fluid palazzo cut. Make a statement without even trying.", 58.99, IMG["trousers"]),
    ("A-Line Denim Skirt — Light Wash", "A classic A-line skirt in a light-wash denim. Sits at the natural waist and falls just below the knee.", 42.99, IMG["jeans"]),
    ("Velvet Flared Trousers — Midnight", "Midnight blue velvet flares with a high waist and flared leg from the knee. Pure 70s glamour.", 72.99, IMG["trousers"]),
    ("Cropped Flare Jeans — Ecru", "A flattering cropped flare in a clean ecru wash. The flare from the knee creates a balanced, elongated silhouette.", 62.99, IMG["jeans"]),
    ("Asymmetric Hem Skirt — Black", "A striking asymmetric hem in fluid crepe. Short at the front, longer at the back — avant-garde and elegant.", 55.99, IMG["trousers"]),
    ("Relaxed Jogger Trousers — Grey", "A premium cotton jogger with a tailored look. Elasticated waist, tapered leg, and side seam pockets.", 38.99, IMG["trousers"]),
    ("Checked Midi Skirt — Green/White", "A bold green and white check print on a flared midi skirt. Button-through front and elastic waistband.", 49.99, IMG["jeans"]),
    ("Tailored Cigarette Trousers — Camel", "Sharp, narrow-cut cigarette trousers in warm camel. Pressed crease, side pockets, and a mid-rise waist.", 67.99, IMG["trousers"]),
    ("Ripped Slim Jeans — Mid Blue", "Lived-in character via deliberate rips at the knee and thigh. Slim fit, mid-blue wash, 5-pocket styling.", 54.99, IMG["jeans"]),
    ("Chiffon Wrap Skirt — Paisley", "A bohemian wrap skirt in sheer paisley-print chiffon. Self-tie waist, easy coverage, and endlessly feminine.", 36.99, IMG["trousers"]),
    ("Wide-Leg Suit Trousers — White", "Power-dressing at its finest. Wide-leg tailored trousers in structured white. Part of a suit or on their own.", 74.99, IMG["trousers"]),
    ("Broderie Anglaise Maxi Skirt", "Delicate broderie anglaise in ivory cotton. A tiered maxi skirt with an elastic waist and a romantic feel.", 66.99, IMG["jeans"]),
    ("Corduroy Mini Skirt — Rust", "Retro wide-wale corduroy in a warm rust tone. A-line mini with a button fly and side pockets.", 38.99, IMG["jeans"]),
    ("Pleated Tennis Skirt — Pink", "A sporty pleated tennis skirt in pastel pink. Built-in shorts underneath for ease and coverage.", 28.99, IMG["activewear"]),
    ("Belted Linen Trousers — Tan", "Relaxed linen trousers with a D-ring belt included. Pleated front, wide-leg, and side-button details.", 69.99, IMG["trousers"]),
    ("Suede Mini Skirt — Camel", "A buttery suede mini skirt in camel with a button-through front and a slight A-line flare.", 62.99, IMG["jeans"]),
    ("Knit Midi Skirt — Rust", "A fine-knit midi skirt in warm rust. Elasticated waist, slight rib texture, and a comfortable drape.", 49.99, IMG["trousers"]),
    ("Patchwork Mini Skirt", "A retro patchwork mini in clashing floral and check prints. Wild, playful, and totally original.", 44.99, IMG["jeans"]),
    ("Midi Slip Skirt — Caramel Satin", "A midi-length slip skirt in glossy caramel satin. Side split, elasticated waist, effortlessly chic.", 52.99, IMG["trousers"]),
    ("Crochet Mini Skirt — Natural", "Hand-crochet mini skirt in natural cotton. A summer festival essential with a boho twist.", 38.99, IMG["jeans"]),
    ("Metallic Pleated Skirt — Bronze", "A mid-length pleated skirt in a metallic bronze fabric. It catches every light in the room.", 74.99, IMG["trousers"]),
    ("Wide-Leg Culottes — Ivory", "Relaxed wide-leg culottes in ivory crepe. A mid-calf length that feels modern and fluid.", 52.99, IMG["trousers"]),
    ("Vintage Wash Flare Jeans", "High-waisted flare jeans in a vintage light wash. The silhouette that flatters every body shape.", 68.99, IMG["jeans"]),
    ("Embroidered Denim Shorts", "Light-wash denim shorts with wildflower embroidery along the pocket edge. Summer perfection.", 36.99, IMG["jeans"]),
    ("Scallop-Edge Shorts — White", "Cotton shorts with a delicate scallop hem and a drawstring waist. Fresh, feminine, and holiday-ready.", 28.99, IMG["trousers"]),
    ("Linen Co-Ord Trousers — Sage", "Wide-leg linen trousers in sage green, designed to coordinate with the matching linen top.", 52.99, IMG["trousers"]),
    ("Neon Cycling Shorts", "Compression cycling shorts in neon yellow with a wide high-waist. Bold and functional.", 28.99, IMG["activewear"]),
    ("Flow Yoga Shorts", "Soft and stretchy flow shorts ideal for yoga and pilates. Short inseam, built-in brief, elasticated waist.", 26.99, IMG["activewear"]),
    ("Waffle Lounge Shorts — Sage", "Waffle-knit lounge shorts in sage green. Elasticated waist and a relaxed fit for easy weekend wear.", 22.99, IMG["lounge"]),
    ("Velour Lounge Shorts — Lilac", "Soft velour lounge shorts in pastel lilac. Wide elasticated waist and a relaxed loose fit.", 24.99, IMG["lounge"]),
    ("Silk Sleep Shorts — Midnight", "Luxurious silk sleep shorts in midnight blue with an elasticated waist. Short and smooth.", 36.99, IMG["lounge"]),
    ("Satin Pyjama Shorts — Black", "Luxurious satin sleep shorts in jet black. Elasticated waist and a mid-thigh length.", 24.99, IMG["lounge"]),
    ("Bamboo Lounge Shorts", "Sustainable bamboo-fibre shorts. Naturally moisture-wicking and temperature-regulating.", 28.99, IMG["lounge"]),
    ("Running Shorts — Coral", "Lightweight 2-in-1 running shorts with inner briefs. Zip pocket, reflective detailing.", 28.99, IMG["activewear"]),
    ("Sports Shorts with Pockets", "Functional training shorts with deep side pockets and an elasticated waistband. Quick-dry fabric.", 24.99, IMG["activewear"]),

    # ── DRESSES (60) ───────────────────────────────────────────────────
    ("Floral Midi Wrap Dress", "A flattering wrap silhouette in a vibrant floral print on fluid crepe. V-neckline, self-tie waist, midi length.", 65.99, IMG["dress_floral"]),
    ("Little Black Dress — Sleeveless", "The ultimate wardrobe staple. A sleeveless, fitted shift dress in matte black crepe. Knee length. Timeless.", 74.99, IMG["dress_midi"]),
    ("Linen Shirt Dress — White", "A relaxed shirt dress in lightweight linen. Belted waist, breast pockets, and a button-through front.", 72.99, IMG["dress_wrap"]),
    ("Satin Slip Dress — Champagne", "Effortlessly sensual. A bias-cut satin slip with adjustable straps and a subtle cowl neck in champagne.", 84.99, IMG["dress_floral"]),
    ("Smocked Boho Maxi — Terracotta", "An earthy terracotta maxi with a smocked bodice and a fluid tiered skirt. Made for warm evenings.", 79.99, IMG["dress_midi"]),
    ("Knit Mini Dress — Chocolate", "A soft ribbed knit mini dress in warm chocolate brown. Long sleeves, fitted through the body.", 58.99, IMG["dress_wrap"]),
    ("Off-Shoulder Ruffle Dress — Coral", "Coral off-shoulder ruffle dress with a tiered skirt and elasticated neckline. Perfect for summer events.", 68.99, IMG["dress_floral"]),
    ("Shirt Dress — Chambray Blue", "A belted chambray shirt dress with roll-tab sleeves and a relaxed, slightly A-line silhouette.", 64.99, IMG["dress_midi"]),
    ("Polka Dot Tea Dress", "Classic black polka dots on a white background. Sweetheart neckline, fitted bodice, and a full midi skirt.", 62.99, IMG["dress_wrap"]),
    ("Velvet Midi Dress — Forest Green", "A rich forest green velvet midi. Long sleeves, V-neckline, and a figure-skimming silhouette.", 94.99, IMG["dress_floral"]),
    ("Blazer Dress — Camel", "A sharp power-dressing choice. A structured camel blazer-dress with oversized lapels and padded shoulders.", 112.99, IMG["dress_midi"]),
    ("Sequin Mini Dress — Silver", "Head-to-toe silver sequins on a bodycon mini silhouette. Spaghetti straps, barely-there glamour.", 89.99, IMG["dress_wrap"]),
    ("Ditsy Floral Sundress", "A sweet ditsy floral on cotton lawn. Gathered waist, thin straps, and a playful midi-length skirt.", 44.99, IMG["dress_floral"]),
    ("Asymmetric Hem Dress — Nude", "A fluid nude dress with a high-low hem. Simple and elegant — the perfect base for statement accessories.", 76.99, IMG["dress_midi"]),
    ("Wrap Dress — Abstract Print", "A bold abstract print on a classic wrap silhouette. V-neck, self-tie belt, and a knee-length skirt.", 67.99, IMG["dress_wrap"]),
    ("Broderie Mini Dress — White", "A breezy broderie anglaise mini with wide shoulder straps and a shirred back for a flexible fit.", 52.99, IMG["dress_floral"]),
    ("Tuxedo Dress — Black", "A fashion-forward tuxedo dress with satin lapels and a self-belt. Sophisticated and endlessly versatile.", 99.99, IMG["dress_midi"]),
    ("Midi Shirt Dress — Sage Stripe", "Vertical sage-and-white stripes on a relaxed midi shirt dress with a belted waist and patch pockets.", 72.99, IMG["dress_wrap"]),
    ("Pleated Chiffon Maxi — Blush", "Flowing pleated chiffon in a delicate blush. Halter neck, open back, and a floor-skimming length.", 105.99, IMG["dress_floral"]),
    ("Denim Pinafore Dress", "A structured denim pinafore with adjustable straps, a square neckline, and a relaxed, above-the-knee length.", 49.99, IMG["dress_midi"]),
    ("Ruched Bodycon Dress — Red", "A dramatic all-over ruched bodycon mini in bold red. Stretch fabric, square neck, and a sleeveless cut.", 54.99, IMG["dress_wrap"]),
    ("Paisley Print Kaftan Dress", "A relaxed kaftan cut in a vivid paisley print. V-neckline, wide sleeves, and a loose-flowing silhouette.", 58.99, IMG["dress_floral"]),
    ("Ponte Fit-and-Flare Dress", "A structured ponte fabric in a fit-and-flare silhouette. Midi length with a concealed back zip.", 82.99, IMG["dress_midi"]),
    ("Crochet Beach Dress — White", "Handcrafted crochet in a relaxed beach-cover style. Wear over a swimsuit or with a slip underneath.", 64.99, IMG["dress_wrap"]),
    ("Longline Knit Dress — Grey Marl", "A cosy longline dress in soft grey marl knit. Funnel neck, long sleeves, and a relaxed shapeless silhouette.", 76.99, IMG["dress_floral"]),
    ("Prom Dress — Dusty Lilac", "Tulle overlay and a fitted bodice in dusty lilac. A dreamy prom-style dress with adjustable spaghetti straps.", 128.99, IMG["dress_midi"]),
    ("Tiered Ruffle Dress — Emerald", "Three tiers of lightweight ruffle in emerald green. A striking statement dress that moves beautifully.", 87.99, IMG["dress_wrap"]),
    ("Pink Gingham Shirt Dress", "A pink gingham co-ord styled as a shirt dress. One piece, easy to wear, perfectly coordinated.", 62.99, IMG["dress_floral"]),
    ("Knitted Slip Dress — Cream", "A delicate knitted slip dress with thin straps and fine rib detailing. Wear alone or over a poloneck.", 56.99, IMG["dress_midi"]),
    ("Burnout Velvet Midi — Plum", "Rich burnout velvet creates a floral pattern on this deep plum midi. Long sleeves and a V-neckline.", 96.99, IMG["dress_wrap"]),
    ("Cotton Wrap Dress — Yellow Floral", "A breezy yellow floral wrap dress in lightweight cotton. Perfect for garden parties and holidays.", 58.99, IMG["dress_floral"]),
    ("Open-Back Midi Dress — Black", "A sleek black midi dress with a dramatic open back and a halter neckline. Evening perfection.", 88.99, IMG["dress_midi"]),
    ("Drawstring Waist Midi Dress", "A drawstring-waist midi in lightweight viscose. Wear cinched or loose for two entirely different looks.", 56.99, IMG["dress_wrap"]),
    ("Long Satin Slip Dress — Blush", "A floor-length blush satin slip with adjustable thin straps and a delicate lace hem.", 88.99, IMG["dress_floral"]),
    ("Strappy Satin Maxi Dress — Sage", "A minimal strappy satin maxi in sage green. Bias cut, body-skimming, and thoroughly elegant.", 98.99, IMG["dress_midi"]),
    ("Puff-Sleeve Mini Dress — Red", "A bold red puff-sleeve mini dress in stretch crepe. Fitted bodice, short hem, dramatic sleeves.", 64.99, IMG["dress_wrap"]),
    ("High-Neck Floral Maxi", "A high-neck maxi dress in a delicate botanical print on white. Long sleeves, a tiered skirt, and an elegant posture.", 86.99, IMG["dress_floral"]),
    ("Velvet Wrap Dress — Champagne", "A champagne velvet wrap dress that skims the body beautifully. Ideal for autumn evenings.", 92.99, IMG["dress_midi"]),
    ("Seersucker Midi Dress — Blue/White", "A breezy seersucker midi in classic blue and white. Square neckline, flutter sleeves, and a full skirt.", 54.99, IMG["dress_wrap"]),
    ("Sequin Column Dress — Gold", "A floor-length column dress entirely in gold sequins. Walk into any room and own it.", 148.99, IMG["dress_floral"]),

    # ── OUTERWEAR (40) ─────────────────────────────────────────────────
    ("Classic Trench Coat — Camel", "A British heritage icon. Double-breasted trench in water-resistant cotton. Storm flap, belt, and epaulettes.", 149.99, IMG["coat"]),
    ("Oversized Blazer — Houndstooth", "A bold houndstooth oversized blazer with sharp shoulders and a relaxed fit. Style open for a cool layered look.", 119.99, IMG["coat"]),
    ("Puffer Jacket — Black", "A lightweight down-filled puffer jacket with a quilted finish. Packable into its own pocket. Very warm.", 89.99, IMG["coat"]),
    ("Teddy Bear Coat — Cream", "Plush faux-shearling teddy coat in warm cream. Oversized and statement-making — a winter hero.", 134.99, IMG["coat"]),
    ("Longline Wool Coat — Charcoal", "A classic longline coat in premium wool blend. Single-breasted, structured shoulders, fully lined.", 179.99, IMG["coat"]),
    ("Denim Jacket — Vintage Wash", "A vintage-washed denim jacket with a worn-in look. Classic trucker silhouette with press-stud closure.", 64.99, IMG["coat"]),
    ("Leather Biker Jacket — Black", "A genuine leather biker jacket with asymmetric zip, quilted shoulders, and multiple buckle details.", 249.99, IMG["coat"]),
    ("Wrap Coat — Rust", "A belted wrap coat in rich rust wool. No buttons — simply tie the waist belt. Elegant and dramatic.", 158.99, IMG["coat"]),
    ("Windbreaker Jacket — Cobalt", "A lightweight ripstop windbreaker in cobalt blue. Packable, water-resistant, and effortlessly cool.", 59.99, IMG["coat"]),
    ("Quilted Gilet — Tan", "A tan quilted gilet for layering over knits. Lightweight insulation, zip-through front, and a sleek finish.", 74.99, IMG["coat"]),
    ("Double-Breasted Wool Blazer — Navy", "A sophisticated double-breasted blazer in navy wool. Structured and sharp — the definition of smart dressing.", 129.99, IMG["coat"]),
    ("Cropped Puffer — Neon Pink", "An ultra-cropped puffer in statement neon pink. Bold and warm — you will not be ignored.", 79.99, IMG["coat"]),
    ("Shearling Aviator Jacket", "A classic aviator jacket with genuine shearling lining and a structured leather exterior. Timeless and warm.", 289.99, IMG["coat"]),
    ("Rain Mac — Sage Green", "A lightweight packable rain mac in sage green. Adjustable hood, press-stud front, and taped seams.", 69.99, IMG["coat"]),
    ("Military Jacket — Khaki", "An oversized military jacket with epaulettes, patch pockets, and a relaxed boxy silhouette.", 84.99, IMG["coat"]),
    ("Colourblock Parka — Green/Black", "A colour-blocked parka in contrasting forest green and black. Faux-fur trimmed hood and sherpa lining.", 112.99, IMG["coat"]),
    ("Cape Coat — Grey", "A dramatic statement cape in grey wool blend. Sleeveless, structured shoulders, sweeping silhouette.", 148.99, IMG["coat"]),
    ("Cotton Canvas Jacket — Stone", "A hardwearing cotton canvas jacket in clean stone. Four patch pockets, snap-button front.", 76.99, IMG["coat"]),
    ("Ribbed Cardigan Coat — Cream", "An elongated ribbed cardigan styled as a coat. Oversized fit, deep pockets, open front with a tie belt.", 92.99, IMG["coat"]),
    ("Bomber Jacket — Leopard Print", "An eye-catching bomber jacket in a bold leopard print. Ribbed cuffs and hem, satin lining.", 94.99, IMG["coat"]),
    ("Longline Leather Coat — Black", "A sleek knee-length leather coat in soft black. Minimal, powerful, and enduring.", 299.99, IMG["coat"]),
    ("Oversized Linen Blazer — White", "A loose, oversized linen blazer in white. Wear over a bikini, a dress, or your favourite jeans.", 89.99, IMG["coat"]),
    ("Teddy Coat — Tan", "A short boxy teddy coat in warm tan faux-shearling. Buttons down the front with patch pockets.", 118.99, IMG["coat"]),
    ("Velvet Blazer — Cobalt Blue", "A rich cobalt velvet blazer with satin-trimmed lapels. A statement piece for bold dressers.", 104.99, IMG["coat"]),
    ("Asymmetric Hem Blazer — Cream", "A cream blazer with a dramatic asymmetric hem — short at the front, longer at the back.", 116.99, IMG["coat"]),
    ("Tailored Linen Blazer — Navy", "A structured navy linen blazer with a single-button front and welt pockets. Essential for summer.", 92.99, IMG["coat"]),
    ("Knitted Crop Jacket — Camel", "A cropped knit jacket in warm camel. Four buttons, rib cuffs and hem — a chic transitional layer.", 62.99, IMG["coat"]),
    ("Longline Padded Coat — Camel", "A statement longline padded coat in camel. Quilted stitching, a hood, and a zip-through front.", 148.99, IMG["coat"]),
    ("Shearling-Collar Denim Jacket", "A classic denim jacket upgraded with a cosy shearling collar lining. The perfect winter layer.", 89.99, IMG["coat"]),
    ("Silk Kimono Robe — Floral", "A luxurious silk kimono robe in a bold floral print. Perfect for mornings, evenings, or a photoshoot.", 78.99, IMG["dress_floral"]),
    ("Cropped Wind Jacket — Yellow", "A cropped technical wind jacket in bold yellow. Packable, water-resistant, with a hidden chest zip.", 58.99, IMG["coat"]),
    ("Cotton Canvas Trench — Tan", "A lightweight cotton canvas trench in tan. Relaxed, everyday-wear take on a true classic.", 119.99, IMG["coat"]),
    ("Check Overshirt Jacket — Grey", "A double-layered check overshirt that works as a light jacket. A transitional season hero.", 74.99, IMG["coat"]),
    ("Quilted Bomber — Sage", "A quilted bomber jacket in sage green. Lightweight and packable with a zip chest pocket.", 72.99, IMG["coat"]),
    ("Collarless Boucle Blazer", "A textured boucle blazer in ivory with a clean, collarless silhouette. Pairs with everything.", 98.99, IMG["coat"]),
    ("Sports Zip Jacket — Grey", "A slim-fit zip-up training hoodie in performance fleece. Thumb-holes, zip pockets, reflective logo.", 54.99, IMG["activewear"]),
    ("Cropped Leather Jacket — Tan", "A cropped tan leather jacket with a zip front and a minimal, clean aesthetic.", 189.99, IMG["coat"]),
    ("Parka — Forest Green", "A knee-length forest green parka with a fur-trim hood and plenty of zip pockets.", 138.99, IMG["coat"]),
    ("Structured Shoulder Blazer — Black", "A sharp black blazer with structured padded shoulders. The foundation of every power look.", 124.99, IMG["coat"]),
    ("Waterproof Snow Jacket — White", "A high-performance waterproof snow jacket in clean white. Technical zips, sealed seams, helmet-compatible hood.", 178.99, IMG["coat"]),

    # ── FOOTWEAR (40) ──────────────────────────────────────────────────
    ("White Leather Trainers", "Clean, minimal white leather trainers with a cushioned sole. The ultimate everyday sneaker.", 79.99, IMG["shoes_trainers"]),
    ("Block-Heel Mules — Tan Suede", "Tan suede mules with a sturdy block heel and a pointed toe. Slip-on ease with a polished finish.", 89.99, IMG["shoes_heels"]),
    ("Platform Chelsea Boots — Black", "A platform Chelsea boot with a chunky lug sole. Elasticated ankle gussets and a pull tab at the back.", 104.99, IMG["shoes_trainers"]),
    ("Strappy Heeled Sandals — Gold", "Delicate gold strappy sandals with a slender heel. A holiday essential and an evening shoe in one.", 69.99, IMG["shoes_heels"]),
    ("Knee-High Boots — Black Leather", "Sleek black leather knee-high boots with a modest heel. Side zip fastening and a pointed toe.", 154.99, IMG["shoes_trainers"]),
    ("Espadrille Wedges — Natural", "Classic espadrille wedges with a jute-wrapped platform and a canvas upper. Summer holiday perfection.", 54.99, IMG["shoes_heels"]),
    ("Retro Running Trainers", "A retro-inspired running trainer with a chunky sole and mixed-material upper. The heritage trainer update.", 94.99, IMG["shoes_trainers"]),
    ("Slingback Court Shoes — Nude", "Classic nude slingbacks with a kitten heel. A French wardrobe essential that elongates the leg beautifully.", 84.99, IMG["shoes_heels"]),
    ("Chunky Loafers — Black", "Oversized platform loafers in black leather with a chunky sole. The ultimate statement shoe.", 112.99, IMG["shoes_trainers"]),
    ("Leather Ankle Boots — Tan", "Tan leather ankle boots with a slim Cuban heel and a side-zip fastening. Versatile and classic.", 124.99, IMG["shoes_heels"]),
    ("Flatform Sandals — White", "White leather flatform sandals with crossover straps and a thick platform sole. Sporty yet feminine.", 67.99, IMG["shoes_trainers"]),
    ("Over-the-Knee Boots — Grey Suede", "Luxury grey suede over-the-knee boots with a modest block heel. Zip at the back ankle.", 178.99, IMG["shoes_heels"]),
    ("Slip-On Canvas Trainers — Ecru", "Minimalist slip-on trainers in ecru canvas. Vulcanised sole, elastic opening, and a clean silhouette.", 42.99, IMG["shoes_trainers"]),
    ("Pointed Stiletto Heels — Red", "A bold statement in bright red. Pointed toe stiletto with a sky-high heel and a smooth finish.", 94.99, IMG["shoes_heels"]),
    ("Birkenstock-Style Sandals — Cork", "A contoured cork footbed sandal with two adjustable buckle straps. Arch support and all-day comfort.", 64.99, IMG["shoes_trainers"]),
    ("Mary Jane Shoes — Black Patent", "Classic black patent Mary Janes with a T-bar strap and a low block heel. Retro charm meets modern wear.", 78.99, IMG["shoes_heels"]),
    ("Flip Flops — Raffia Beige", "Woven raffia flip flops with a flat sole and a leather toe post. The lightest summer sandal.", 29.99, IMG["shoes_trainers"]),
    ("Cowboy Boots — Brown Leather", "Genuine leather cowboy boots with a pointed toe and stitched shaft detailing. Pull tabs for easy wear.", 189.99, IMG["shoes_heels"]),
    ("High-Top Trainers — Sage Green", "High-top trainers in sage green with white detailing and a cushioned ankle collar.", 82.99, IMG["shoes_trainers"]),
    ("Barely-There Heeled Sandals", "Ultra-minimal strappy heeled sandals with barely-there thin straps and a square toe.", 76.99, IMG["shoes_heels"]),
    ("Platform Derby Shoes — Black", "Chunky platform derby shoes with a lace-up front and a thick crepe sole. Grunge meets grown-up.", 96.99, IMG["shoes_trainers"]),
    ("Shearling-Lined Slippers — Tan", "Sheepskin-lined slippers in tan suede. Warm, hardwearing, and incredibly comfortable.", 42.99, IMG["shoes_heels"]),
    ("Loafer Mules — Cognac Leather", "Slip-on loafer mules in cognac leather with a gold bit detail. Sophisticated and wearable.", 112.99, IMG["shoes_heels"]),
    ("Platform Flip Flops — Black", "Chunky platform flip flops in black with a thick EVA sole and webbing straps.", 34.99, IMG["shoes_trainers"]),
    ("Woven Ankle Sandals — Tan", "Woven leather ankle sandals with a flat sole and a buckle fastening. Artisan-crafted summer style.", 67.99, IMG["shoes_heels"]),
    ("Pointed Mule Heels — Snake", "Pointed-toe mule heels in a subtle snakeskin effect. Kitten heel, easy slip-on, and very chic.", 78.99, IMG["shoes_heels"]),
    ("Kitten Heel Mules — Ivory", "Elegant ivory kitten heel mules with a pointed toe and a buckle-detail strap.", 74.99, IMG["shoes_heels"]),
    ("Open-Toe Block Heel Sandal", "A square open-toe sandal with a sturdy block heel and an ankle-wrap strap.", 72.99, IMG["shoes_heels"]),
    ("Platform Espadrilles — Black", "Black canvas espadrilles with a chunky platform sole and ankle-tie ribbons.", 59.99, IMG["shoes_trainers"]),
    ("Ankle Strap Wedge Sandals", "Nude ankle-strap wedge sandals with a jute platform sole. Comfortable and elegant.", 68.99, IMG["shoes_heels"]),
    ("Leopard Print Loafers", "Leopard print loafers with a low block heel. A bold statement piece that works with everything.", 89.99, IMG["shoes_heels"]),
    ("Raffia-Woven Sandal Flats", "Flat sandals with a raffia-woven upper and a leather footbed. Artisan style for warm days.", 49.99, IMG["shoes_heels"]),
    ("Wrap Trainers — White/Tan", "Minimalist wrap-style trainers with a tan leather trim on a clean white base.", 84.99, IMG["shoes_trainers"]),
    ("Plush Slippers — Blush", "Memory foam insole slippers with a plush faux-fur upper in blush. Your feet will thank you.", 29.99, IMG["shoes_trainers"]),
    ("Hiking-Style Chunky Trainers", "Rugged chunky sole trainers with technical lacing and a trail-inspired upper. Street-ready.", 104.99, IMG["shoes_trainers"]),
    ("Ballet Flats — Satin Cream", "Simple satin ballet flats in cream with an elasticated topline and a ribbon tie detail.", 54.99, IMG["shoes_heels"]),
    ("Chelsea Boots — Chelsea Tan", "Classic tan leather Chelsea boots with elasticated side gussets and a stacked heel.", 134.99, IMG["shoes_trainers"]),
    ("Strappy Gladiator Sandals", "Leather gladiator sandals with multiple straps up the ankle. A confident, bold summer sandal.", 62.99, IMG["shoes_heels"]),
    ("Knitted Sock Boots — Black", "Stretch-knit sock boots in black with a pointed toe and block heel. A sleek, modern silhouette.", 88.99, IMG["shoes_heels"]),
    ("Chunky Sneakers — Pastel", "An oversized pastel chunky sneaker with a sculptural sole and mixed-material upper.", 96.99, IMG["shoes_trainers"]),

    # ── BAGS (40) ──────────────────────────────────────────────────────
    ("Mini Crossbody Bag — Tan", "A perfectly compact tan leather crossbody. Adjustable chain strap, interior card slot, and magnetic closure.", 89.99, IMG["bag_shoulder"]),
    ("Oversized Tote — Canvas", "A roomy waxed canvas tote with leather handles and a zip closure. Perfect for the market, beach, or office.", 64.99, IMG["bag_tote"]),
    ("Structured Top-Handle Bag — Black", "A structured leather bag with a top handle and a detachable crossbody strap. Clean lines, timeless style.", 134.99, IMG["bag_shoulder"]),
    ("Woven Straw Basket Bag", "Handwoven straw with leather trim and a double top handle. Summer's most essential arm candy.", 54.99, IMG["bag_tote"]),
    ("Chain Shoulder Bag — Gold/Black", "A quilted-effect flap bag with a long gold chain strap. Glamorous and surprisingly spacious inside.", 112.99, IMG["bag_shoulder"]),
    ("Caramel Leather Backpack", "A structured caramel leather backpack with two external pockets and a padded laptop compartment.", 148.99, IMG["bag_tote"]),
    ("Raffia Clutch — Natural", "A woven raffia clutch with a tortoiseshell clasp. Summer evening perfect — holds your essentials beautifully.", 42.99, IMG["bag_shoulder"]),
    ("Baguette Bag — Burgundy", "A slim baguette-style bag in rich burgundy leather with a flap closure and a short shoulder strap.", 96.99, IMG["bag_tote"]),
    ("Clear Vinyl Crossbody", "A contemporary clear vinyl crossbody with leather trim and a zip closure. Bold, modern, and unique.", 44.99, IMG["bag_shoulder"]),
    ("Weekend Duffel — Navy Canvas", "A large navy canvas duffel with leather base and handles. Plenty of room for a weekend away.", 84.99, IMG["bag_tote"]),
    ("Box Bag — White Leather", "A structured white leather box bag with a gold chain and a hinged clasp. Architecture you can carry.", 158.99, IMG["bag_shoulder"]),
    ("Bucket Bag — Tan Suede", "A drawstring bucket bag in soft tan suede with a crossbody strap. Casual elegance at its finest.", 78.99, IMG["bag_tote"]),
    ("Micro Mini Bag — Lilac", "Tiny and cute. A micro-mini bag in lilac leather — more of an accessory than a bag, and that is the point.", 56.99, IMG["bag_shoulder"]),
    ("Shopper Tote — Cognac", "A spacious cognac leather shopper with dual handles and interior organisation pockets.", 104.99, IMG["bag_tote"]),
    ("Leather Fanny Pack — Black", "A sleek leather fanny pack with adjustable strap, zip pocket, and a press-stud closure.", 52.99, IMG["bag_shoulder"]),
    ("Velvet Evening Bag — Emerald", "A plush emerald velvet evening bag with a jewel-encrusted clasp. Small, precious, and utterly beautiful.", 74.99, IMG["bag_tote"]),
    ("Half-Moon Bag — Beige", "A curved half-moon silhouette in beige pebbled leather. Crossbody strap and a push-lock closure.", 92.99, IMG["bag_shoulder"]),
    ("Mesh Tote — Black/Gold", "A stylish mesh tote in black with gold hardware. See-through panels give a contemporary, urban feel.", 47.99, IMG["bag_tote"]),
    ("Doctor Bag — Racing Green", "A structured doctor-style bag in racing green leather. Top handles, a zip top, and a vintage feel.", 118.99, IMG["bag_shoulder"]),
    ("Drawstring Pouch Bag — Ivory", "A silky drawstring pouch bag in ivory. Minimal, versatile, and elegant as a clutch or crossbody.", 38.99, IMG["bag_tote"]),
    ("Quilted Crossbody — Pink", "A quilted pink crossbody with a silver chain strap and a magnetic flap closure. Chic and compact.", 84.99, IMG["bag_shoulder"]),
    ("Snakeskin-Print Crossbody", "A snakeskin-effect print crossbody in tan and cream. A subtle print with big style impact.", 64.99, IMG["bag_tote"]),
    ("Structured Saddle Bag — Brown", "A structured brown leather saddle bag with a front flap and adjustable strap. Classic and versatile.", 118.99, IMG["bag_shoulder"]),
    ("Canvas Weekend Bag — Olive", "A spacious olive canvas weekend bag with leather trim, zip closure, and a shoe compartment.", 78.99, IMG["bag_tote"]),
    ("Monogram Shoulder Bag — Tan", "A tan leather shoulder bag with monogram-style embossed detailing and a long adjustable strap.", 94.99, IMG["bag_shoulder"]),
    ("Glitter Clutch Bag — Gold", "A hard-shell glitter clutch in gold. The bag you take out on the nights you want to shine.", 44.99, IMG["bag_tote"]),
    ("Reversible Tote — Black/Camel", "A reversible leather tote in black on one side, camel on the other. Two bags for the price of one.", 96.99, IMG["bag_shoulder"]),
    ("Beaded Bag Strap — Rainbow", "A detachable rainbow beaded bag strap that fits most bags. Customise your existing bag instantly.", 19.99, IMG["bag_tote"]),
    ("Woven Raffia Mini Bag", "A tiny handwoven raffia bag with a bamboo handle. A joyful, artisan-made summer statement.", 36.99, IMG["bag_shoulder"]),
    ("Leather Card Holder — Black", "A slim black leather card holder with four card slots and a central cash compartment.", 24.99, IMG["bag_tote"]),

    # ── JEWELLERY (40) ─────────────────────────────────────────────────
    ("White Ceramic Hoop Earrings", "Minimal and elegant handcrafted ceramic hoops that complement both casual and formal looks beautifully.", 12.99, IMG["earring_w"]),
    ("Pearl Drop Earrings", "Classic baroque pearls on a sterling silver drop setting. Timeless sophistication for every occasion.", 24.99, IMG["earring_pearl"]),
    ("Diamond & Emerald Chandelier Earrings", "Show-stopping chandelier earrings set with brilliant-cut diamonds and rich emerald accents.", 89.99, IMG["earring_gem"]),
    ("Layered Gold Necklace Set", "Three delicate gold-tone chains in varying lengths designed to be worn together. Minimal and modern.", 34.99, IMG["earring_w"]),
    ("Chunky Silver Chain Necklace", "A bold chunky chain necklace in polished silver. Makes a statement solo or layered with finer chains.", 28.99, IMG["earring_pearl"]),
    ("Birthstone Pendant — Amethyst", "A deep purple amethyst set in a sterling silver pendant. Delicate chain included. Perfect as a gift.", 44.99, IMG["earring_gem"]),
    ("Wide Gold Cuff Bracelet", "A wide polished gold cuff with an open-sided design. Wear alone for maximum impact.", 36.99, IMG["earring_w"]),
    ("Stacked Ring Set — Silver", "A set of five stackable sterling silver rings. Mix and match for your perfect combination.", 22.99, IMG["earring_pearl"]),
    ("Crystal Stud Earrings — Clear", "Sparkling clear crystal studs in a claw setting on sterling silver posts. Simple, brilliant, timeless.", 18.99, IMG["earring_gem"]),
    ("Tennis Bracelet — Gold/CZ", "A classic tennis bracelet with rows of cubic zirconia set in gold-plated silver. Glamour every day.", 58.99, IMG["earring_w"]),
    ("Ear Cuff — Rose Gold", "A rose gold ear cuff that wraps the upper ear with no piercing required. Edgy and elegant.", 14.99, IMG["earring_pearl"]),
    ("Lapis Lazuli Surfer Bracelet", "Small lapis lazuli and silver bead bracelet. A laid-back, boho-inspired look with a natural feel.", 16.99, IMG["earring_gem"]),
    ("Feather Drop Earrings — Gold", "Delicate gold-plated feather earrings that catch the light with every movement. Boho and beautiful.", 19.99, IMG["earring_w"]),
    ("Black Velvet Choker Necklace", "A classic black velvet choker with a gold medallion pendant centrepiece. Effortlessly stylish.", 12.99, IMG["earring_pearl"]),
    ("Signet Ring — Gold Plated", "A flat-face gold-plated signet ring. Personalise or wear as-is — a classic with staying power.", 29.99, IMG["earring_gem"]),
    ("Statement Hoop Earrings — Gold", "Oversized polished gold hoops. Bold and wearable — the earrings that go with literally everything.", 24.99, IMG["earring_w"]),
    ("Gemstone Cocktail Ring — Ruby", "A large oval ruby-red gemstone in a silver prong setting. A cocktail ring for special moments.", 48.99, IMG["earring_pearl"]),
    ("Gold Heart Locket Necklace", "A heart-shaped locket in gold with room for two small photos. A deeply personal and sentimental gift.", 37.99, IMG["earring_gem"]),
    ("Star Charm Bracelet", "A delicate gold bracelet with star-shaped charms throughout. A meaningful everyday piece.", 21.99, IMG["earring_w"]),
    ("Crescent Moon Pendant", "A simple crescent moon pendant in sterling silver on an adjustable chain. Spiritual and stylish.", 19.99, IMG["earring_pearl"]),
    ("Emerald Cocktail Ring", "A bold emerald-cut stone in a sleek gold setting. The ring that elevates every outfit.", 54.99, IMG["earring_gem"]),
    ("Gold Hoop Set — 3 Sizes", "A trio of gold-plated hoop earrings in small, medium, and large sizes. Mix or wear one at a time.", 18.99, IMG["earring_w"]),
    ("Multi-Strand Pearl Choker", "A three-strand faux pearl choker with a gold clasp. Classic, bold, and infinitely versatile.", 26.99, IMG["earring_pearl"]),
    ("Crystal Drop Pendant", "A faceted crystal pendant suspended on a fine gold chain. Catches and refracts the light beautifully.", 32.99, IMG["earring_gem"]),
    ("Tassel Earrings — Gold", "Long cascading tassel earrings in gold tone. Lightweight and dramatic — made to be noticed.", 16.99, IMG["earring_w"]),
    ("Pearl Hair Clip Set", "A set of four pearl-encrusted hair clips in gold tone. For effortless elegant hairstyles.", 15.99, IMG["earring_pearl"]),
    ("Beaded Bracelet — Malachite", "Green malachite bead bracelet with a sterling silver clasp. A natural, earthy accessory.", 24.99, IMG["earring_gem"]),
    ("Velvet Scrunchie Set — Jewel Tones", "A set of five velvet scrunchies in rich jewel tones — emerald, sapphire, ruby, amethyst, and gold.", 12.99, IMG["earring_w"]),
    ("Embellished Headband — Gold", "A flexible gold headband encrusted with rhinestones. Bridal, festival, or everyday — it works.", 17.99, IMG["earring_pearl"]),
    ("Padded Headband Set — Neutrals", "Four padded headbands in a mix of neutral tones — everyday hair essentials with a refined look.", 16.99, IMG["earring_gem"]),

    # ── ACCESSORIES (30) ───────────────────────────────────────────────
    ("Cashmere Scarf — Camel", "Pure cashmere in a classic camel tone. Incredibly soft and warm, this scarf is a lifelong investment.", 84.99, IMG["scarf"]),
    ("Wide-Brim Sun Hat — Straw", "A handwoven straw wide-brim sun hat with a black grosgrain band. Chic sun protection.", 39.99, IMG["hat"]),
    ("Silk Hair Scrunchie Set — 3 Pack", "Three silk scrunchies in complementary tones — ivory, blush, and sage. Gentle on hair, beautiful to wear.", 18.99, IMG["scarf"]),
    ("Leather Belt — Tan", "A classic single-prong leather belt in rich tan. Silver buckle, multiple sizing eyelets.", 34.99, IMG["hat"]),
    ("Cat-Eye Sunglasses — Black", "Retro cat-eye frames in polished black acetate with dark grey lenses. UV400 protection.", 42.99, IMG["scarf"]),
    ("Merino Wool Beanie — Forest Green", "A ribbed-knit merino wool beanie in rich forest green. Warm, itch-free, and impeccably styled.", 28.99, IMG["hat"]),
    ("Satin Eye Mask — Lavender", "A silky satin eye mask with adjustable elastic. Block light beautifully, look good doing it.", 14.99, IMG["scarf"]),
    ("Knitted Gloves — Burgundy", "Soft knitted gloves in deep burgundy with a subtle cable-knit pattern. Warm and elegant.", 22.99, IMG["hat"]),
    ("French Navy Beret", "A classic French beret in navy boiled wool. Structured yet relaxed — effortless Parisian style.", 26.99, IMG["scarf"]),
    ("Gold Waist Chain Belt", "An adjustable gold chain waist belt. Dress it over a jumper or dress for an instant waist-defining effect.", 19.99, IMG["hat"]),
    ("Tortoiseshell Hair Claw Clip", "A large resin hair claw in a warm tortoiseshell pattern. Effortless updo, zero effort required.", 9.99, IMG["scarf"]),
    ("Oversized Square Sunglasses", "Large-frame square sunglasses in translucent tortoise acetate. Classic and effortlessly cool.", 48.99, IMG["hat"]),
    ("Satin Bow Hair Clip — Ivory", "A large satin bow hair clip in ivory. Clip it to a bun or low ponytail for a sweet, polished look.", 8.99, IMG["scarf"]),
    ("Velvet Headband — Emerald", "A plush velvet headband in deep emerald. Holds hair back neatly while making a serious style statement.", 12.99, IMG["hat"]),
    ("Leopard Print Silk Scarf", "A classic leopard print on lightweight silk. Tie around the neck, the bag, or the hair for instant glamour.", 44.99, IMG["scarf"]),
    ("Round Sunglasses — Green Lens", "Round retro frames with mirrored green lenses. Lightweight metal frame and UV400 protection.", 36.99, IMG["hat"]),
    ("Faux Fur Earmuffs — Pink", "Fluffy pink faux fur earmuffs on a flexible metal headband. Cosy and cute for winter.", 16.99, IMG["scarf"]),
    ("Patterned Socks Set — 5 Pairs", "Five pairs of patterned cotton socks in a coordinating mix of stripes, dots, and botanicals.", 19.99, IMG["hat"]),
    ("Canvas Baseball Cap — Ecru", "A relaxed-fit canvas baseball cap in clean ecru with a subtle tonal logo embroidery.", 24.99, IMG["scarf"]),
    ("Leather Wrist Wallet — Black", "A slim leather wrist wallet that slips over the hand for hands-free essentials.", 28.99, IMG["hat"]),
    ("Geometric Print Silk Scarf", "A geometric print in bold jewel tones on 100% silk. Wear around the neck, wrist, or hair.", 54.99, IMG["scarf"]),
    ("Wrap-Around Sunglasses — White", "Sporty wrap-around sunglasses in white with blue mirrored lenses. UV400 certified.", 48.99, IMG["hat"]),
    ("Wide-Brim Fedora — Black", "A black felt wide-brim fedora with a grosgrain band. The hat that makes any outfit 10x cooler.", 42.99, IMG["hat"]),
    ("Colour-Pop Bucket Hat — Orange", "A structured bucket hat in bold orange cotton. Sun-protective and endlessly cool.", 19.99, IMG["scarf"]),
    ("Fluffy Knit Beret — Cream", "An impossibly soft fluffy-knit beret in cream. A statement head piece for colder days.", 21.99, IMG["hat"]),
    ("Snap-Back Cap — Black", "A classic snap-back cap in black with a curved brim and a woven brand patch at the front.", 22.99, IMG["scarf"]),
    ("Over-Knee Socks — 3 Pack", "Three pairs of ribbed over-the-knee socks in natural, grey, and black. Cosy and collegiate.", 18.99, IMG["hat"]),
    ("Woven Leather Belt — Cognac", "An intricate woven-leather belt in cognac with a gold pin buckle. Handcrafted and beautiful.", 44.99, IMG["scarf"]),
    ("Cashmere Blend Bedsocks", "Incredibly soft cashmere-blend bedsocks with a ribbed design and non-slip sole. Pure luxury for your feet.", 18.99, IMG["hat"]),
    ("Tortoiseshell Wide Headband", "A wide resin headband in tortoiseshell. A statement accessory that keeps hair back in style.", 13.99, IMG["scarf"]),

    # ── ACTIVEWEAR (30) ────────────────────────────────────────────────
    ("High-Waist Leggings — Black", "Four-way stretch high-waist leggings with a sculpting waistband. Squat-proof, moisture-wicking.", 44.99, IMG["activewear"]),
    ("Sports Bra — Sage Green", "Medium-impact sports bra with a wide underband and adjustable straps. Breathable mesh back panel.", 28.99, IMG["activewear"]),
    ("Seamless Workout Set — Lilac", "A matching seamless sports bra and legging set in soft lilac. Buttery-smooth fabric, minimal seams.", 64.99, IMG["activewear"]),
    ("High-Impact Sports Bra — Black/White", "A high-impact padded sports bra with removable cups and a racerback design. Full support guaranteed.", 36.99, IMG["activewear"]),
    ("Wide-Leg Yoga Pants — Dusty Rose", "Wide-leg yoga pants in a buttery soft fabric. Wide waistband, relaxed and flowy fit.", 39.99, IMG["activewear"]),
    ("Zip-Up Training Hoodie", "A slim-fit zip-up training hoodie in performance fleece. Thumb-holes, zip pockets, reflective logo.", 54.99, IMG["hoodie"]),
    ("Cycling Shorts — Navy", "Compression cycling shorts with a wide high-waist and anti-chafe inner seams. Versatile and flattering.", 32.99, IMG["activewear"]),
    ("Performance Crop Top — Mint", "A fitted performance crop top in moisture-wicking mint fabric. Built-in bra, square neckline.", 24.99, IMG["activewear"]),
    ("Longline Sports Jacket — Grey", "A longline knitted sports jacket with a half-zip and relaxed fit. The gym-to-coffee essential.", 62.99, IMG["hoodie"]),
    ("Leopard Print Leggings", "Bold leopard print leggings in four-way stretch fabric. High waist, squat-proof, and incredibly flattering.", 47.99, IMG["activewear"]),
    ("Mesh Panel Sports Set", "A colour-blocked sports set with mesh panel detailing at the sides. Crop top and mid-rise shorts.", 56.99, IMG["activewear"]),
    ("Thermal Running Tights — Black", "Wind-resistant thermal running tights with a fleece-lined interior and reflective details.", 52.99, IMG["activewear"]),
    ("Training Tank — White", "A loose-fit training tank with racerback detailing and a dropped armhole. Ultra-breathable.", 18.99, IMG["activewear"]),
    ("Pilates Grip Socks — 3 Pack", "Three pairs of non-slip grip socks for Pilates and yoga. Silicone grips on the sole, ankle-height.", 16.99, IMG["activewear"]),
    ("Printed Leggings — Tie-Dye", "Vibrant hand-dye inspired print on high-performance leggings. Moisture-wicking and flattering.", 48.99, IMG["activewear"]),
    ("Cropped Wind Jacket — Neon Yellow", "An ultra-cropped neon yellow wind jacket. Packable, water-resistant, and very visible.", 58.99, IMG["coat"]),
    ("Oversized Gym Sweatshirt — Pink", "A heavyweight oversized sweatshirt in blush pink. Perfect post-workout or as a cosy off-duty piece.", 44.99, IMG["hoodie"]),
    ("Full-Length Yoga Set — Earth Tones", "A coordinated yoga set in warm earth tones — full-length leggings and a longline sports bra.", 72.99, IMG["activewear"]),
    ("Compression Running Leggings", "Full-length compression running leggings with a high waist and reflective detailing.", 54.99, IMG["activewear"]),
    ("Workout Crop Top — Cobalt Blue", "A fitted workout crop top in cobalt blue with a cross-back strap design.", 29.99, IMG["activewear"]),
    ("Neon Yellow Sports Set", "A matching neon yellow sports bra and legging set. High-visibility and high-performance.", 58.99, IMG["activewear"]),
    ("Flared Yoga Pants — Terracotta", "High-waist flared yoga pants in a warm terracotta hue. Perfect for yoga, walks, and everything in between.", 46.99, IMG["activewear"]),
    ("Seamless Ribbed Gym Set — Black", "A seamless ribbed black sports bra and legging set. Sleek, compressive, and professional.", 68.99, IMG["activewear"]),
    ("Long Sleeve Running Top — Cobalt", "A slim-fit long sleeve running top with flatlock seams and reflective detailing.", 36.99, IMG["activewear"]),
    ("Sports Bra — Coral", "A medium-impact sports bra in bold coral. Wide non-slip straps and a moisture-wicking lining.", 28.99, IMG["activewear"]),
    ("High-Waist Bike Shorts — Grey", "Smooth compression bike shorts in grey with a flattering high waist. Great for cycling, Pilates, or yoga.", 32.99, IMG["activewear"]),
    ("Zip-Neck Long Sleeve Base Layer", "A slim-fit base layer in technical fabric with a quarter-zip neck and moisture management.", 42.99, IMG["activewear"]),
    ("Sports Vest — Black", "A simple black sports vest with a relaxed cut and a scooped hem. Ultra-breathable for training.", 16.99, IMG["activewear"]),
    ("Cropped Zip Hoodie — Sage", "A cropped half-zip hoodie in sage green fleece. Great for layering at the gym or on a cold morning.", 44.99, IMG["hoodie"]),
    ("Dance Leggings — Holographic", "Holographic sheen on high-performance leggings. Bold, technical, and absolutely unique.", 56.99, IMG["activewear"]),

    # ── LOUNGEWEAR (30) ────────────────────────────────────────────────
    ("Satin Pyjama Set — Blush", "A classic satin pyjama set in soft blush pink. Long-sleeve button-through top and wide-leg trousers.", 58.99, IMG["lounge"]),
    ("Fleece Robe — Dove Grey", "An ultra-plush fleece robe in dove grey. Deep pockets, a shawl collar, and a self-tie belt.", 64.99, IMG["lounge"]),
    ("Cotton Pyjama Set — Navy Stripe", "Classic navy and white striped pyjamas in 100% cotton. Button-through top and drawstring trousers.", 44.99, IMG["lounge"]),
    ("Ribbed Lounge Set — Chocolate", "A matching ribbed lounge set in warm chocolate brown. Cropped top and wide-leg trousers.", 52.99, IMG["lounge"]),
    ("Sherpa Zip Hoodie — Ecru", "A cosy sherpa-lined hoodie in ecru with a full zip. The softest thing you will ever own.", 72.99, IMG["hoodie"]),
    ("Linen Pyjamas — Ivory", "Relaxed linen pyjamas in natural ivory. Breathable and lightweight — perfect for warm nights.", 56.99, IMG["lounge"]),
    ("Knit Cardigan Robe — Oatmeal", "A longline open-front knit robe in warm oatmeal. Cosy enough for lounging, stylish enough for Zoom calls.", 67.99, IMG["lounge"]),
    ("Bamboo Pyjama Set — Soft Pink", "Eco-friendly bamboo-fibre pyjamas in soft pink. Incredibly breathable and temperature-regulating.", 62.99, IMG["lounge"]),
    ("Velour Tracksuit Set — Berry", "A matching velour tracksuit in deep berry. Zip-up jacket and elasticated joggers. Y2K-inspired luxury.", 74.99, IMG["lounge"]),
    ("Longline Knit Loungewear Top", "A longline oversized knit top with dropped shoulders and ribbed detailing. Wear over leggings or pyjamas.", 38.99, IMG["lounge"]),
    ("French Terry Sweatpants — Stone", "Heavyweight French terry sweatpants in warm stone. Elasticated waist, tapered leg, and side pockets.", 42.99, IMG["lounge"]),
    ("Oversized Sleep Shirt — Check", "A roomy sleep shirt in cosy brushed cotton check. Long enough to wear as a dress, comfortable enough to sleep in.", 28.99, IMG["lounge"]),
    ("Cotton Nightdress — White", "A simple white cotton nightdress with a pintuck collar and lace trim. Classic, comfortable, and elegant.", 34.99, IMG["lounge"]),
    ("Oversized Fluffy Jumper — Cream", "An ultra-soft fluffy knit jumper in cream. Oversized fit with ribbed cuffs and hem. Pure comfort.", 56.99, IMG["lounge"]),
    ("Ribbed Pyjama Short Set — Mauve", "A matching ribbed short and cami set in mauve. Great for warm nights or layered under a robe.", 32.99, IMG["lounge"]),
    ("Teddy Bear Pyjama Set — Mushroom", "A super-soft teddy-fabric pyjama set in a muted mushroom tone. Short top and jogger trousers.", 48.99, IMG["lounge"]),
    ("Silk Kimono Robe — Floral Print", "A floaty silk kimono robe in bold floral print. Wear it as a beach cover-up or a luxurious layer.", 82.99, IMG["dress_floral"]),
    ("Cosy Knit Jogger Set — Blue", "A matching knit jogger set in dusty blue — relaxed top and elasticated trousers. Weekend perfection.", 68.99, IMG["lounge"]),
    ("Longline Lounge Cardigan — Sage", "A soft open-front longline cardigan in sage green. Luxurious lounging, not obvious loungewear.", 62.99, IMG["lounge"]),
    ("Ribbed Hoodie Dress — Charcoal", "An oversized hoodie dress in charcoal ribbed jersey. Pockets, a drawstring hood, and ultimate comfort.", 52.99, IMG["hoodie"]),
    ("Waffle-Knit Robe — Blush", "A waffle-knit cotton robe in blush with a tie-belt and two patch pockets. Spa-quality, home-priced.", 54.99, IMG["lounge"]),
    ("Cashmere Blend Socks — Cream", "Cashmere-blend bed socks in cream with a ribbed cuff. Endlessly cosy for cold nights.", 18.99, IMG["lounge"]),
    ("Satin Shorts Pyjama Set — Navy", "A satin cami and shorts set in navy blue. Lightweight and cool for warm nights.", 46.99, IMG["lounge"]),
    ("Cloud Print Pyjamas", "Soft brushed cotton pyjamas printed with a dreamy cloud pattern. Cosy without being kitsch.", 42.99, IMG["lounge"]),
    ("Ruched Longline Lounge Dress", "A longline lounge dress with ruched side detailing. Soft jersey, relaxed fit, knee length.", 44.99, IMG["lounge"]),
    ("Tie-Dye Lounge Set", "A matching tie-dye hoodie and jogger set. Relaxed, colourful, and perfectly coordinated.", 58.99, IMG["lounge"]),
    ("Wide-Leg Pyjama Trousers — Ditsy", "Wide-leg pyjama trousers in a ditsy floral cotton. Pull-on waist and a cosy, relaxed fit.", 28.99, IMG["lounge"]),
    ("Plush Slippers — Sage", "Memory foam insole slippers with a plush faux-fur upper in sage green. A step above ordinary.", 29.99, IMG["lounge"]),
    ("Long Sleeve Lounge Top — Mushroom", "A soft jersey long-sleeve top in warm mushroom. The perfect companion to loungewear bottoms.", 24.99, IMG["lounge"]),
    ("Short-Sleeve Pyjama Set — Ivory", "A crisp ivory pyjama short set in cotton poplin. Minimal and polished for restful nights.", 38.99, IMG["lounge"]),

    # ── Jumpers & Knitwear ─────────────────────────────────────────────────
    ("Chunky Cable Knit Jumper — Oatmeal", "A generously oversized cable-knit jumper in warm oatmeal. Thick yarn, relaxed fit, cosy enough for the coldest days.", 72.99, IMG["coat"]),
    ("Fine Knit Roll-Neck — Camel", "A fine-gauge roll-neck jumper in rich camel. Slim but comfortable, layers beautifully under coats and blazers.", 54.99, IMG["coat"]),
    ("Mohair Blend Jumper — Lilac", "A fluffy mohair-blend jumper in dreamy lilac. Wear loose over wide-leg trousers for effortless weekend dressing.", 79.99, IMG["lounge"]),
    ("Argyle Knit Vest — Green/Cream", "A classic argyle knit vest in forest green and cream. Layer over a white shirt or dress it up solo.", 44.99, IMG["shirt_white"]),
    ("Cropped Knit Cardi — Dusty Rose", "A cropped cardigan with pearl-effect buttons in dusty rose. Perfect over high-waisted jeans or a floral midi.", 49.99, IMG["lounge"]),
    ("Oversized Fisherman Knit — Ecru", "A classic fisherman-stitch oversized jumper in ecru. Authentic texture, cosy warmth, and a timeless silhouette.", 84.99, IMG["shirt_white"]),
    ("Polo-Neck Ribbed Jumper — Black", "A slim-fit polo-neck in fine black ribbed jersey. Sleek, sophisticated, and pairs with absolutely everything.", 58.99, IMG["shirt_black"]),
    ("Rainbow Stripe Jumper", "A bold rainbow-stripe jumper in soft cotton knit. Colourful, fun, and guaranteed to brighten any outfit.", 52.99, IMG["lounge"]),
    ("Longline Knit Jumper Dress — Terracotta", "A knee-length knit jumper dress in warm terracotta. Ribbed hem and cuffs, relaxed fit, wear with ankle boots.", 74.99, IMG["dress_midi"]),
    ("V-Neck Fair Isle Jumper — Multi", "A classic Fair Isle jumper with a V-neck in multicolour. Traditional pattern, modern fit.", 67.99, IMG["lounge"]),
    ("Sheer Knit Layer — Ivory", "A gossamer-weight knit layer in ivory. Wear over a cami or under a blazer for textural interest.", 46.99, IMG["blouse"]),
    ("Ribbed Turtleneck — Olive", "A classic ribbed turtleneck in muted olive. Pairs with everything from midi skirts to wide-leg trousers.", 42.99, IMG["shirt_black"]),
    ("Cropped Crew-Neck Sweatshirt — Stone", "A premium French terry cropped crew-neck in warm stone. Minimal branding, maximum comfort.", 38.99, IMG["hoodie"]),

    # ── Blazers & Tailoring ────────────────────────────────────────────────
    ("Double-Breasted Blazer — Cream", "A structured double-breasted blazer in cream. Sharp lapels, a nipped waist, and polished enough for the office.", 119.99, IMG["coat"]),
    ("Oversized Pinstripe Blazer — Charcoal", "A relaxed oversized blazer in charcoal pinstripe. Wear with matching trousers or contrast with jeans.", 134.99, IMG["coat"]),
    ("Linen Blazer — Sage", "A relaxed single-button linen blazer in sage green. Light, breathable, and effortlessly summer-appropriate.", 98.99, IMG["coat"]),
    ("Velvet Blazer — Midnight Blue", "A rich velvet blazer in midnight blue. Party-ready with its jewel-tone lustre and slim fit.", 124.99, IMG["coat"]),
    ("Tweed Blazer — Pink/Cream", "A classic boucle tweed blazer in pink and cream. Timeless tailoring for a polished finish.", 149.99, IMG["coat"]),
    ("Cropped Blazer — Caramel", "A cropped single-breasted blazer in warm caramel. Structured shoulders, cinched waist.", 108.99, IMG["coat"]),
    ("Check Blazer — Brown/Tan", "A heritage-check single-breasted blazer in brown and tan tones. Classic British tailoring.", 129.99, IMG["coat"]),
    ("Satin Blazer — Champagne", "A sleek satin blazer in champagne. Doubles as evening wear; pairs with matching trousers.", 116.99, IMG["blouse"]),
    ("Boyfriend Blazer — Navy", "A relaxed boyfriend-cut blazer in classic navy. Great over a white tee and straight-leg jeans.", 94.99, IMG["coat"]),

    # ── Skirts ─────────────────────────────────────────────────────────────
    ("Pleated Midi Skirt — Sage", "A pleated midi skirt in soft sage green crepe. Fluid movement, elasticated waist, sits at the knee.", 54.99, IMG["dress_midi"]),
    ("Denim Mini Skirt — Mid Wash", "A classic denim mini skirt in mid wash. Button-front detail, A-line silhouette.", 42.99, IMG["jeans"]),
    ("Satin Bias-Cut Midi Skirt — Blush", "A bias-cut satin midi skirt in blush pink. Floaty, elegant, and unexpectedly versatile.", 62.99, IMG["dress_wrap"]),
    ("Leather-Look Pencil Skirt — Black", "A high-waisted leather-look pencil skirt in black. Sleek and figure-hugging with a centre-back split.", 56.99, IMG["trousers"]),
    ("Tiered Boho Maxi Skirt — Terracotta", "A tiered cotton maxi skirt in terracotta with subtle broderie trim. Bohemian, flowy, and holiday-ready.", 58.99, IMG["dress_floral"]),
    ("Check Mini Skirt — Black/White", "A tailored black and white check mini skirt with a kick pleat.", 46.99, IMG["trousers"]),
    ("Sequin Mini Skirt — Gold", "A fully-sequinned mini skirt in gold. The centrepiece of any evening outfit.", 72.99, IMG["shoes_heels"]),
    ("Corduroy A-Line Midi Skirt — Rust", "An A-line midi skirt in soft rust corduroy. Pockets included. Autumnal perfection.", 52.99, IMG["coat"]),
    ("Lace Trim Slip Skirt — Champagne", "A satin slip skirt with delicate lace hem in champagne.", 58.99, IMG["blouse"]),
    ("Broderie Anglaise Mini Skirt — White", "A white cotton mini skirt with broderie anglaise detailing. Fresh and feminine for summer.", 44.99, IMG["dress_floral"]),
    ("Faux Suede Wrap Skirt — Tobacco", "A wrap-front faux suede midi skirt in tobacco brown. Rich texture and flattering drape.", 59.99, IMG["coat"]),

    # ── Tops & Blouses ─────────────────────────────────────────────────────
    ("Silk Cami Top — Champagne", "A bias-cut silk cami in champagne. Wear tucked into trousers or layered under a blazer.", 62.99, IMG["blouse"]),
    ("Off-Shoulder Ruffle Top — White", "A cotton off-shoulder top with ruffle trim in white. Romantic and feminine for summer.", 38.99, IMG["blouse"]),
    ("Broderie Blouse — Sky Blue", "A relaxed broderie anglaise blouse in sky blue. Puffed sleeves, a breezy fit, and holiday-appropriate.", 46.99, IMG["blouse"]),
    ("Wrap Front Top — Terracotta", "A jersey wrap-front top in warm terracotta. Flattering neckline and adjustable tie.", 34.99, IMG["blouse"]),
    ("Linen Button-Down Blouse — Sage", "A relaxed linen button-down blouse in sage green. Roll up the sleeves and wear tucked into denim.", 42.99, IMG["linen_shirt"]),
    ("Pussy-Bow Blouse — Ivory", "A pussy-bow blouse in crisp ivory satin. Polished and professional with a feminine touch.", 54.99, IMG["blouse"]),
    ("Ribbed Halter Neck Top — Black", "A fitted ribbed halter neck in black. Minimal, sleek, and perfect for layering.", 28.99, IMG["shirt_black"]),
    ("Smocked Peasant Top — Floral", "A smocked peasant top in a pretty floral print. Elasticated bust and hem, floaty sleeves.", 36.99, IMG["dress_floral"]),
    ("Tie-Front Crop Top — Gingham", "A cute tie-front crop top in black and white gingham. Wear with high-waisted shorts or a midi skirt.", 28.99, IMG["blouse"]),
    ("Corset-Style Boned Top — Blush", "A structured boned corset-style top in blush. Adjustable lace-up back, strapless silhouette.", 54.99, IMG["blouse"]),
    ("Striped Crop Top — Navy/White", "A classic navy and white Breton stripe crop top. Simple, chic, and eternally stylish.", 24.99, IMG["shirt_white"]),
    ("Balloon-Sleeve Blouse — Lilac", "A cotton blouse with dramatic balloon sleeves in lilac. Statement dressing for everyday occasions.", 52.99, IMG["blouse"]),

    # ── Shoes & Footwear ───────────────────────────────────────────────────
    ("Block-Heel Mules — Cream", "Slip-on mules with a comfortable block heel in cream leather. Chic, minimal, and all-day wearable.", 89.99, IMG["shoes_heels"]),
    ("White Leather Sneakers", "Classic low-top leather sneakers in white. Clean, minimal, and endlessly versatile.", 74.99, IMG["shoes_trainers"]),
    ("Chelsea Boots — Tan", "Pull-on Chelsea boots in tan leather with elasticated side panels. A timeless British wardrobe essential.", 119.99, IMG["shoes_heels"]),
    ("Platform Sandals — Black", "Strappy platform sandals in black. Comfortable platform sole adds height without sacrificing comfort.", 84.99, IMG["shoes_heels"]),
    ("Pointed-Toe Kitten Heels — Blush", "Elegant pointed-toe kitten heels in soft blush suede. Understated, feminine, and office-appropriate.", 96.99, IMG["shoes_heels"]),
    ("Canvas Lace-Up Trainers — Sage", "Relaxed canvas lace-up trainers in sage green. A casual cool alternative to your standard white trainers.", 52.99, IMG["shoes_trainers"]),
    ("Over-Knee Boots — Black", "Sleek over-the-knee boots in black faux leather. Make a statement with skinny jeans or a mini skirt.", 134.99, IMG["shoes_heels"]),
    ("Strappy Heeled Sandals — Gold", "Thin-strap heeled sandals in gold metallic. Perfect for weddings, parties, and summer evenings.", 92.99, IMG["shoes_heels"]),
    ("Loafers — Chocolate Brown", "Classic leather loafers in chocolate brown. Wear with tailored trousers, jeans, or even skirts.", 98.99, IMG["shoes_heels"]),
    ("Running Trainers — White/Pink", "Lightweight running trainers in white with pink detailing. Performance meets style.", 88.99, IMG["shoes_trainers"]),

    # ── Bags & Accessories ─────────────────────────────────────────────────
    ("Mini Crossbody Bag — Black", "A compact black leather crossbody bag with a gold chain strap. Goes with everything.", 68.99, IMG["bag_shoulder"]),
    ("Woven Straw Tote — Natural", "A woven straw tote bag in natural. Spacious enough for a beach day, stylish enough for the market.", 44.99, IMG["bag_tote"]),
    ("Structured Handbag — Camel", "A structured top-handle handbag in camel leather. Timeless, elegant, and effortlessly put-together.", 118.99, IMG["bag_shoulder"]),
    ("Canvas Backpack — Olive", "A lightweight canvas backpack in olive with leather trim. Everyday practical with a fashion-forward edge.", 56.99, IMG["bag_tote"]),
    ("Velvet Evening Clutch — Emerald", "A rich emerald velvet clutch with a gold frame clasp. The finishing touch for any special occasion.", 52.99, IMG["bag_shoulder"]),
    ("Quilted Chain Bag — Pink", "A small quilted shoulder bag with a chain strap in pastel pink.", 88.99, IMG["bag_shoulder"]),
    ("Oversized Shopper — Cream", "A spacious cream canvas shopper with leather handles. Minimal branding, maximum versatility.", 46.99, IMG["bag_tote"]),
    ("Raffia Basket Bag", "A handwoven raffia basket bag with leather handles. Perfect for farmers markets and beach trips.", 62.99, IMG["bag_tote"]),
    ("Belt Bag — Black", "A sleek black belt bag that converts to a crossbody. Hands-free convenience with minimal aesthetic.", 48.99, IMG["bag_shoulder"]),

    # ── Jewellery ───────────────────────────────────────────────────────────
    ("Gold Hoop Earrings — Large", "Classic large gold hoop earrings. Lightweight, durable, and instantly elevating for any look.", 28.99, IMG["earring_gem"]),
    ("Layered Necklace Set — Gold", "A set of three layered gold necklaces at varying lengths. Mix and match or wear together.", 36.99, IMG["earring_gem"]),
    ("Chunky Chain Bracelet — Silver", "A bold chunky chain bracelet in silver-tone metal. Makes a statement solo or stacked.", 22.99, IMG["earring_gem"]),
    ("Butterfly Stud Earrings — Gold", "Delicate butterfly-motif stud earrings in gold. Dainty, charming, and suitable for everyday wear.", 18.99, IMG["earring_gem"]),
    ("Statement Cocktail Ring — Clear Stone", "A large faceted clear stone cocktail ring in a gold setting. Maximalist jewellery.", 24.99, IMG["earring_gem"]),
    ("Pearl Anklet", "A delicate faux pearl anklet on a gold chain. Wear barefoot or with sandals.", 16.99, IMG["earring_pearl"]),
    ("Tortoiseshell Claw Clips — Set of 3", "A set of three tortoiseshell claw clips in different sizes. Essential for effortless updos.", 14.99, IMG["earring_gem"]),
    ("Teardrop Drop Earrings — Amethyst", "Elegant teardrop drop earrings featuring an amethyst-coloured stone in a gold setting.", 26.99, IMG["earring_gem"]),
    ("Initial Pendant Necklace — Gold", "A dainty initial pendant necklace on a fine gold chain. A personalised touch.", 32.99, IMG["earring_pearl"]),
    ("Crystal Hair Pins — Set of 6", "A set of six bobby pins with crystal embellishments. Perfect for bridal updos.", 11.99, IMG["earring_pearl"]),

    # ── Scarves, Hats & Misc ───────────────────────────────────────────────
    ("Oversized Wool Wrap — Camel", "A luxuriously oversized wool wrap in camel. Wear as a scarf, shawl, or blanket.", 64.99, IMG["scarf"]),
    ("Leopard Print Silk Scarf", "A classic leopard print silk scarf. Tie in your hair, around your neck, or on your bag handle.", 38.99, IMG["scarf"]),
    ("Checked Blanket Scarf — Red/Black", "A generous tartan blanket scarf in red and black. Wrap around twice for ultimate winter warmth.", 42.99, IMG["scarf"]),
    ("Bucket Hat — Sage", "A cotton twill bucket hat in sage green. Sun protection with understated style.", 22.99, IMG["hat"]),
    ("Wide-Brim Sun Hat — Natural", "A wide-brim straw sun hat in natural. Elegant and practical for beach days.", 34.99, IMG["hat"]),
    ("Knitted Beanie — Camel", "A ribbed knit beanie in camel. Soft, stretchy, and perfect for cold-weather styling.", 18.99, IMG["hat"]),
    ("Baseball Cap — White", "A structured cotton baseball cap in white. Minimal logo, adjustable strap.", 24.99, IMG["hat"]),
    ("Beret — Black", "A classic wool beret in black. A Parisian wardrobe essential.", 28.99, IMG["hat"]),
    ("Silk Hair Scrunchie — Set of 4", "A set of four silk scrunchies in muted jewel tones. Gentle on hair, beautiful as accessories.", 16.99, IMG["scarf"]),
    ("Leather Gloves — Tan", "Lined leather gloves in tan with a button detail at the wrist. Elegant and practical.", 48.99, IMG["scarf"]),
    ("Belted Leather Waist Belt — Black", "A classic leather waist belt in black with a gold buckle. Cinches in any look.", 32.99, IMG["scarf"]),
    ("Sunglasses — Tortoiseshell Oval", "Retro oval sunglasses with tortoiseshell acetate frames. UV400 protection with a vintage aesthetic.", 44.99, IMG["scarf"]),


    # ── Final top-up products ───────────────────────────────────────────────
    ("Wrap Midi Dress — Forest Green", "A flowing wrap midi dress in forest green with a V-neckline and tie waist. Elegant for any occasion.", 72.99, IMG["dress_wrap"]),
    ("Smock Dress — Yellow Floral", "A sunny yellow floral smock dress with elasticated chest. Easy, breezy summer dressing.", 54.99, IMG["dress_floral"]),
    ("Bodycon Mini Dress — Red", "A ribbed bodycon mini dress in bold red. Fitted, confident, and perfect for a night out.", 44.99, IMG["activewear"]),
    ("Slip Dress — Chocolate", "A minimal satin slip dress in rich chocolate brown. Pairs beautifully with a leather jacket.", 66.99, IMG["dress_wrap"]),
    ("Blazer Dress — Camel", "A structured single-breasted blazer dress in camel. Wear with heels for a powerful workwear look.", 94.99, IMG["coat"]),
    ("Puff Sleeve Mini Dress — Lilac", "A cotton mini dress with puff sleeves in soft lilac. Sweet, feminine, and easy to wear.", 48.99, IMG["blouse"]),
    ("Knit Polo Dress — White", "A ribbed knit polo dress in white. Sporty-chic with a collar and button placket.", 58.99, IMG["shirt_white"]),
    ("Linen Shirt Dress — Khaki", "A relaxed linen shirt dress in khaki. Belted or open, it works equally well either way.", 68.99, IMG["linen_shirt"]),
    ("Sequin Midi Dress — Silver", "A floor-grazing sequin midi dress in silver. The ultimate party statement piece.", 118.99, IMG["shoes_heels"]),
    ("Broderie Maxi Dress — White", "A white cotton broderie anglaise maxi dress with a fitted bodice and flowing skirt.", 82.99, IMG["dress_floral"]),
    ("Halter Neck Dress — Cobalt Blue", "A fluid halter neck midi dress in cobalt blue. Bold colour, minimal design, maximum impact.", 74.99, IMG["activewear"]),
    ("Plisse Pleated Dress — Sage", "A plisse-textured pleated midi dress in sage. The pleating adds movement and visual interest.", 78.99, IMG["dress_midi"]),
    ("Ruched Bodycon Dress — Nude", "A ruched bodycon dress in nude with a gathered side detail. Flattering and polished.", 54.99, IMG["activewear"]),
    ("Off-Shoulder Maxi — Ivory", "A cotton off-shoulder maxi dress in ivory with a ruffled hem. Holiday perfection.", 84.99, IMG["dress_floral"]),
    ("Contrast Stitch Straight Jeans", "High-rise straight-leg jeans with visible contrast stitching. Contemporary denim styling.", 58.99, IMG["jeans"]),
    ("Wide-Leg Linen Trousers — Cream", "Relaxed wide-leg linen trousers in cream. Breathable, effortless, and incredibly versatile.", 54.99, IMG["trousers"]),
    ("Tailored Flare Trousers — Black", "High-waisted flare trousers in black with a pressed centre crease. Polished seventies styling.", 68.99, IMG["trousers"]),
    ("Utility Cargo Trousers — Khaki", "Relaxed cargo trousers in khaki with patch pockets. Functional, on-trend, and easy to style.", 62.99, IMG["trousers"]),
    ("Paperbag Waist Trousers — Rust", "Paperbag-waist trousers in warm rust with wide-leg cut. Cinch with the tie belt for definition.", 56.99, IMG["trousers"]),
    ("Pinstripe Wide-Leg Trousers — Charcoal", "Sleek pinstripe wide-leg trousers in charcoal. Classic tailored suiting fabric.", 74.99, IMG["trousers"]),
    ("Barrel-Leg Jeans — Light Blue", "Oversized barrel-leg jeans in light blue. The relaxed silhouette that has taken over fashion week.", 64.99, IMG["jeans"]),
    ("Straight-Leg Jeans — Indigo", "Classic straight-leg jeans in rich indigo denim. Clean wash, no distressing, eternally stylish.", 56.99, IMG["jeans"]),
    ("Crop Flare Jeans — Mid Blue", "Cropped flare jeans with a high rise in mid blue. Vintage-inspired with a modern-fit update.", 58.99, IMG["jeans"]),
    ("Leather-Look Trousers — Caramel", "Faux leather wide-leg trousers in caramel. Luxe-looking, surprisingly comfortable.", 72.99, IMG["trousers"]),
    ("High-Waist Mom Jeans — Black", "Classic black mom jeans with a high waist and tapered leg. A denim wardrobe essential.", 54.99, IMG["jeans"]),
    ("Longline Wool Coat — Camel", "A floor-length double-faced wool coat in classic camel. Structured, warm, and eternally stylish.", 219.99, IMG["coat"]),
    ("Quilted Jacket — Olive", "A lightweight quilted jacket in olive. Compressible, warm, and perfect for layering.", 88.99, IMG["coat"]),
    ("Faux Fur Gilet — Cream", "A plush faux fur gilet in cream. Adds warmth and luxurious texture to any outfit.", 98.99, IMG["coat"]),
    ("Shearling Collar Coat — Brown", "A structured coat with a shearling collar in warm brown. Cosy luxury for winter.", 178.99, IMG["coat"]),
    ("Cropped Puffer Jacket — Black", "A cropped puffer jacket in black. Lightweight insulation for cold days without the bulk.", 94.99, IMG["coat"]),
    ("Trench Coat — Stone", "A classic double-breasted trench coat in stone. The ultimate heritage outerwear piece.", 168.99, IMG["coat"]),
    ("Biker Jacket — Black", "A fitted biker jacket in black faux leather with silver zip detailing. The ultimate cool-girl layer.", 128.99, IMG["coat"]),
    ("Bomber Jacket — Sage", "A satin bomber jacket in sage green with ribbed cuffs and hem. Relaxed, retro, and easy to wear.", 94.99, IMG["coat"]),
    ("Denim Jacket — Bleached", "A bleached denim jacket with a relaxed oversized fit. A summer wardrobe staple.", 68.99, IMG["jeans"]),
    ("Fur-Trim Parka — Khaki", "A longline parka in khaki with a faux-fur trimmed hood. Seriously warm for winter.", 148.99, IMG["coat"]),
    ("Yoga Leggings — Navy", "High-waisted yoga leggings in smooth navy. Four-way stretch, squat-proof, and moisture-wicking.", 42.99, IMG["activewear"]),
    ("Sports Bra — Coral", "A medium-support sports bra in coral with a racerback. Flattering fit for yoga and pilates.", 32.99, IMG["activewear"]),
    ("Athletic Shorts — Black", "Lightweight athletic shorts in black with an inner liner. Versatile for gym, running, or casual wear.", 28.99, IMG["activewear"]),
    ("Zip-Up Hoodie — Grey Marl", "A classic zip-up hoodie in grey marl. Soft brushed interior, relaxed fit.", 46.99, IMG["hoodie"]),
    ("Seamless Gym Set — Dusty Pink", "A matching seamless legging and sports bra set in dusty pink. Squat-proof and sweat-wicking.", 64.99, IMG["activewear"]),

]

assert len(products) >= 500, f"Only {len(products)} products — need 500"

# Shuffle for variety in the grid view
random.seed(42)
random.shuffle(products)
products = products[:500]

cur.executemany(
    'INSERT INTO products (name, description, price, image_url) VALUES (?, ?, ?, ?)',
    products
)
print(f"Inserted {len(products)} products.")

# ── Demo user ────────────────────────────────────────────────────────
DEMO_USERNAME = "demo"
DEMO_PASSWORD = "Demo1234!"
DEMO_EMAIL    = "demo@shopapp.com"

hashed_pw = generate_password_hash(DEMO_PASSWORD, method='pbkdf2:sha256', salt_length=16)
cur.execute(
    'INSERT INTO Users (username, password, email) VALUES (?, ?, ?)',
    (DEMO_USERNAME, hashed_pw, DEMO_EMAIL)
)
demo_id = cur.lastrowid
print(f"Demo user created (id={demo_id}).")

# Demo basket — 5 items
for pid, qty in [(1,2),(4,1),(7,3),(12,1),(20,2)]:
    cur.execute('INSERT INTO Basket (user_id, product_id, quantity) VALUES (?,?,?)', (demo_id, pid, qty))

# Demo wishlist — 8 items
for pid in [2, 5, 9, 15, 22, 31, 45, 60]:
    cur.execute('INSERT INTO Favorites (user_id, product_id) VALUES (?,?)', (demo_id, pid))

# Sample reviews
reviews = [
    (demo_id, 1,  "Absolutely love it!",        "Perfect fit and the quality is outstanding. Already ordered a second one. Highly recommend."),
    (demo_id, 4,  "My summer favourite",         "This is my go-to piece this summer. Lightweight, flattering, gets so many compliments. The colour is even better in person."),
    (demo_id, 7,  "Great quality",               "Exactly as described. Delivery was fast and the packaging was beautiful. Will definitely be shopping here again."),
    (demo_id, 12, "Pleasantly surprised",        "A little unsure ordering online but the quality is genuinely impressive. Looks even better than in the photos."),
    (demo_id, 20, "Perfect gift",                "Bought this as a gift and the recipient was absolutely delighted. Would give 6 stars if I could."),
    (demo_id, 2,  "Versatile wardrobe staple",   "Wear this with everything. Fabric is soft and comfortable all day. Washed really well — no shrinkage at all."),
    (demo_id, 9,  "Stunning piece",              "Really beautiful product. The craftsmanship is excellent and it looks far more expensive than the price suggests."),
    (demo_id, 15, "Even better in person",       "Photos do not do this justice. In real life the colour depth and texture are gorgeous. Very happy."),
]
cur.executemany(
    'INSERT INTO review (user_id, product_id, name, description) VALUES (?,?,?,?)',
    reviews
)
print(f"Sample reviews added ({len(reviews)}).")

con.commit()
con.close()

print()
print("=" * 55)
print("  DATABASE READY — productdb.db")
print("=" * 55)
print(f"  Products  : 500")
print(f"  Reviews   : {len(reviews)}")
print()
print("  DEMO USER CREDENTIALS")
print("  ─────────────────────────────────────")
print(f"  Username  : {DEMO_USERNAME}")
print(f"  Password  : {DEMO_PASSWORD}")
print(f"  Email     : {DEMO_EMAIL}")
print()
print("  HOW TO RUN THE APP")
print("  ─────────────────────────────────────")
print("  1.  pip install -r requirements.txt")
print("  2.  python seed-db.py           (this file)")
print("  3.  python app.py")
print("  4.  Open http://127.0.0.1:5000")
print("=" * 55)
