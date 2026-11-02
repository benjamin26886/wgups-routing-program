# WGUPS Routing Program — Final Report

## A. Algorithm Identification

I picked the **Nearest Neighbor algorithm** for this project. It's a type of greedy algorithm, and the reason I landed on it is because it maps really well to how you'd actually think about delivering packages in real life. Like, if you're standing at a delivery stop and you've got a truck full of packages, you're probably just going to look at your list and drive to whichever address is closest to where you already are. That's basically what this algorithm does — it checks the distance to every remaining stop, picks the shortest one, goes there, and then does the whole thing over again from the new spot.

It's not going to find the mathematically perfect route every time. Algorithms that do that take way too long because they'd have to check every possible ordering of stops, and with 40 packages that's a ridiculous number of permutations. But the Nearest Neighbor approach gets close enough. My total mileage came out to 113 miles, which is comfortably under the 140-mile requirement. The TSP (Traveling Salesman Problem) is a classic computer science problem and this greedy heuristic is one of the standard ways people tackle it without blowing up the runtime (Cormen et al., 2009).

What makes it self-adjusting is that there's no pre-planned route. After each delivery the truck basically says "okay, where am I now, and what's closest?" — so the route reshapes itself as packages get dropped off.

## B. Data Structure Identification

For storing all the package data I wrote a **chaining hash table** by hand. I know Python already has dictionaries that do essentially the same thing, but the rubric asks for a custom implementation so I built one from the ground up. Mine uses separate chaining, meaning each slot in the table holds a little list. When two package IDs happen to hash to the same slot, the second one just gets tacked onto that list instead of causing problems (Cormen et al., 2009).

### B1. How the Data Structure Accounts for Data Relationships

Each package has a bunch of attributes tied to it — the address where it needs to go, the city, zip code, what time it's due by, how much it weighs, any special notes from the manifest, and then a status that my program updates as things happen ("At Hub" at first, then "En Route" once the truck leaves, then "Delivered at 09:14" or whatever the actual time ends up being).

The address, deadline, city, zip code, weight and status all get stored together in the hash table, and I use the **Package ID** as the key. (The extra routing details like the notes, the truck number and the delivery time are kept in a small `PackageRecord` object next to the table.) So when my code needs to, say, check what address package 14 goes to during routing, it just hashes the number 14 and pulls that package's data out of the right bucket. Same thing when I need to fix Package 9's address partway through — I look up 9, change the address field, done. Without the hash table I'd be writing for-loops to search through a list every time I needed one package's info, which would get old fast with 40 packages and three trucks all needing constant lookups.

## C. Program Overview

### C1. Algorithm Logic — Pseudocode

```
LOAD all 40 packages from the CSV into a hash table, using Package ID as key
LOAD the distance table and list of addresses from the other CSV

CREATE three Truck objects
    each gets a list of package IDs to carry, a departure time, and
    starts at the Hub address (4001 South 700 East)

FUNCTION deliver_packages(truck):
    grab all the truck's packages from the hash table, put them in
    an "unvisited" list

    WHILE there are still packages in unvisited:
        set shortest_distance to infinity
        set next_package to nothing

        FOR each package left in unvisited:
            check distance from truck's current location to package address
            IF that distance is less than shortest_distance:
                update shortest_distance and mark this as next_package

        add shortest_distance to truck's odometer
        move the truck to next_package's address
        figure out how much time that trip took (distance / 18 mph)
            and advance the truck's clock
        stamp the delivery time on the package
        pull next_package out of the unvisited list

    IF this truck's driver needs to go back to the hub afterward:
        drive back and add that distance to the odometer too
```

### C2. Development Environment

I did everything in **Python 3** with **Visual Studio Code** as my editor. My computer is just a regular laptop with an Intel processor, 16 gigs of RAM, and an SSD. The program honestly finishes in like a fraction of a second so the hardware doesn't really matter here — even a pretty old machine would handle it fine.

The main reason I picked VSCode over something like PyCharm is the debugger. I kept running into this problem early on where packages with a 10:30 deadline were showing up as delivered at like 10:45, and I couldn't figure out why just by reading the code. So I started dropping breakpoints inside the while loop in deliver_packages and stepping through it one delivery at a time. I could hover over the variables and see exactly which package the algorithm was about to pick and what distance it calculated. Turned out I had a truck loading issue, not a routing issue — once I moved those packages to an earlier truck it was fine. I also just kept the terminal open in VSCode the whole time so I could rerun the program after every small change without switching windows.

### C3. Space-Time Complexity (Big-O)

I'll go through the main parts of the program one at a time.

The CSV loading part is simple — I read each of the 40 package rows and stick them in the hash table. Inserting one package is O(1) on average because the hash function tells me exactly which bucket to use, so doing all 40 is **O(N)**. Storage is **O(N)** too since I keep one Package object per row. The distance table is a fixed 27×27 grid that I read into a 2D list, and because 27 never changes (the city has a set number of delivery locations) I basically treat that as constant.

The routing is the heavy part. When the truck is deciding where to go first, it checks distances to every package on board. After dropping one off, it checks every remaining package again. So the first pass looks at N packages, the next pass looks at N-1, then N-2, all the way down to 1. Add those up and you get roughly N²/2, which in Big-O terms is **O(N²)**. I spent a while trying to figure out if there was a way around this but the thing is, Nearest Neighbor has to compare against all remaining options each time — that's kind of the whole point. Memory-wise the routing barely uses anything extra, just a couple variables tracking the current best pick, so that's **O(1)** auxiliary.

The user interface part — when someone types in a time and wants to see where all the packages are — just does 40 hash table lookups in a row. Each one is **O(1)** average.

So altogether: **O(N²)** time because the routing dwarfs everything else, **O(N)** space for the hash table and the package objects stored in it.

### C4. Scalability and Adaptability

Forty packages is nothing for this program. It runs instantly and the mileage stays well under the limit, so there's definitely room to scale up some. The hash table side of things would handle growth fine — you can keep throwing packages into it and the chaining just absorbs any extra collisions. Eventually you'd want to make the bucket array bigger to keep the chains short, but the structure itself won't break or anything (Cormen et al., 2009).

The routing side is a different story though. With 40 packages the O(N²) loop is instant, and even a couple hundred would probably be fine. But if WGUPS suddenly had to handle, I don't know, five thousand packages in a day? That squared term would actually start to hurt. I wouldn't scrap the algorithm entirely if that happened — I'd probably just divide Salt Lake City into a grid first, maybe north/south/east/west quadrants or something based on zip codes, and then run Nearest Neighbor inside each quadrant separately. That way no single run of the algorithm ever deals with more than a manageable chunk of deliveries.

### C5. Software Efficiency and Maintainability

I have three classes in the code — `PackageRecord` for the routing details of each package, `Truck` for tracking each vehicle's state, and `ChainingHashTable` for the storage backend. The deliver_packages function sits outside all of them and just takes a truck as input. I structured it that way on purpose because I didn't want changing one thing to accidentally break something else. My OOP textbook talks a lot about this idea of separation of concerns (Lysecky & Vahid, 2018) and it definitely made my life easier during testing.

Say WGUPS gets a new truck that can carry 20 packages instead of 16. All I'd change is the list of package IDs that gets passed to the Truck constructor. The deliver_packages function doesn't know or care how many packages are loaded — it just works through whatever's there. Or say they expand to a new city. Swap the two CSV files for ones with the new addresses and distances, and the code runs the same without touching a single line of Python. That kind of flexibility is the whole point of not hardcoding things.

### C6. Strengths and Weaknesses of the Hash Table

The biggest thing going for the hash table is speed. Every time the routing loop needs to check a package's address, that's a hash table lookup. Every time a package gets delivered and I need to stamp the time on it, another lookup. With three trucks each making 11-16 stops, those lookups add up, and the fact that each one is O(1) on average means it never becomes a bottleneck. I also leaned on this heavily for the Package 9 fix — at 10:20 I just looked up package 9 by ID, changed two fields, and was done. If I'd used a regular list I would've had to write a search loop for that, which is annoying more than anything. The chaining part is a plus too because I never had to worry about what happens when two IDs land in the same bucket. They both just sit there in a little list, no data gets lost.

On the flip side, there's no ordering. I realized this when I was debugging and wanted to see all the packages sorted by their deadline — the hash table couldn't just give me that. I had to pull everything out into a separate list and sort it myself. Not a dealbreaker for this project but it's a real limitation. The other concern is more theoretical: right now I have 40 packages in 40 buckets so collisions are rare, but if the number of packages grew a lot without expanding the table, you'd get longer and longer chains in each bucket and lookups would creep toward O(N) instead of O(1) (Cormen et al., 2009).

### C7. Key Justification

I went with **Package ID** as the hash table key. I did think about the other options before settling on this.

The first thing I asked myself was: which of these fields is actually unique for every single package? Because if two packages share the same key value, one of them is going to get overwritten or at minimum cause a collision that slows things down. And when I looked at the data, most of the other fields failed that test immediately. A bunch of packages share addresses — 26 and 38 go to the exact same place on 5383 S 900 East, for example. Almost everything is in Salt Lake City, so city is out. Zip codes repeat all over the place. Deadlines are mostly either 10:30 AM or EOD so you'd have massive collision pileups there. Weight has duplicates too.

Delivery status is actually the worst option and it took me a second to realize why. It's not just non-unique — it actively changes while the program runs. A package starts as "At Hub," then I mark it "En Route" when the truck leaves, then it becomes "Delivered at" whatever time. If that were my key, the package would essentially move to a different bucket every time its status updated, and I'd lose track of it completely.

Package ID doesn't have any of these problems. Every package gets a unique number, it's an integer so it hashes cleanly with the modulo operator, and it stays the same from start to finish. Plus it's how a real person would query the system — you'd call in asking about package 9, not asking about "the 2-pound package going to 84111" (Cormen et al., 2009).

---

## D. Sources

Cormen, T. H., Leiserson, C. E., Rivest, R. L., & Stein, C. (2009). *Introduction to algorithms* (3rd ed.). MIT Press.

Lysecky, R., & Vahid, F. (2018). *C++ programming: From problem analysis to program design*. zyBooks. https://www.zybooks.com

Western Governors University. (n.d.). *WGUPS routing program scenario and data files* [Course materials]. WGU.

---

## E. Professional Communication

I tried to write this report so that someone grading it can find each rubric item without having to hunt for it — the section headings match the assignment letters and numbers directly. I used technical vocabulary where it was needed (things like Big-O, hash table, greedy algorithm) but I also tried to explain what those terms actually mean in context rather than just dropping them in. Citations follow APA formatting and are listed in Section D.
