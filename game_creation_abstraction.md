# Game Creation - Abstractions


## Turn Based Games

## Players, Information
 * N players
 * zero sum competitive vs. players competing against AI
 * Non-zero sum perhaps means players can accumulate winnings over time, with proportional winnings doled out to players each round
    * but in each round, is there a zero sum? If some players win, it means others must lose (which could be "dealer"/AI)

 * Is AI/dealer another player or does it have special rules?
 * Does it use randomness rather than strategy?
 * Imperfect vs perfect information
    * sub: amongst players, or between players and dealer
    * or among everyone (poker- some information is known only to each player, some information is not known by any player or even the dealer, the card deck)
 * Is each turn the same?
 * Does each player have the same, opposite, or orthogonal goals?
 * Are there rounds that are somehow connected, or is each round completely independent? ("superstructure")
 * Psychological? Can players form alliances or is it beneficial to do so?
   * what would the abstraction for this be?
   * perhaps sharing of information or resources between players:
     * catan, trade happens. trade is sharing resources or powers. information is also selectively shared, but once it's shared it's shared with everyone. no private sharing between 2 players only
     * in catan information and resource sharing in the middle of the game can help both players, but later on only a single player can win
     * poker, no sharing is allowed and probably no sharing is beneficial. Implicit sharing is encouraged as players imagine probabilistically what others could have in their hand. Bluffing possible, but not outright lying
     * secret hitler or mafia: information can be shared but often not proved. is lying possible? Some of this information can have varying degrees of probabilistic certainty, which varies between players (if p1 gives mixed F/L cards to p2, p1 knows p2 can choose two options. But others do not know this, and p2 might convince people that he was dealt 2 F cards)
 * Are there teams? How many?
 * can multiple players win?
## Board structures:
   * graph
     * directed vs undirected
     * levels of connection/degree of nodes
     * traversal vs placement/removal
     * static vs dynamic
       * is the graph built over the course of the game?
         - dominoes, scrabble
       * Or "filled in"?
         - Chess, Go
     * is graph filled in over time? Most games have this
    * significance/complexity of nodes or pawns placed on nodes
      * chess has complex rules/roles applied to dynamic pawns
      * go has very simple rules applied to static tokens
      * lifetime of pawns/tokens. can they be removed?
    * portions of nodes "owned" or "visible" to certain players
      * pandemic: players only have access to certain nodes at a time, given by their hand and pawns on board
   * simple sets of tokens without significant structure besides sequential reveals of new elements
     * poker
     * hearts
     * fishbowl
   * are there multiple graphs? Why?
   * other structures possible, mostly subsets of graph:
     * tree(s)
     * lines or linked lists

## Winning Conditions
  * single play vs rounds
  * minimax - opposite winning critera, common in two player games like chess, checkers, go
  * win as many points or as few points during subrounds (hearts, spades, euchre)
  * create certain complex topological structure in filled-in graph
    * common in games with simple rules, to balance out that simplicity (Go - surround one color with other color)
    * connect 4, tic tac toe
  * remove all pawns [of certain type] from board (pandemic, chess)
  * be dealt the best hand (= set of tokens) from ordered set of good hands based on probability (poker)
    * Poker: game is to predict relative strengths of each hand in play, with wagered+formalized confidence by means of betting with imperfect information
  * guess unknown tokens with varying degrees of probability and imperfect information
    * sometimes within time
    * fishbowl, taboo
    * help from other players or your team
      * codenames (with very specific amount of information communicated by team - taboo, codenames)
  * run out of tokens in hand after placing on board (scrabble, dominoes)
  * separate winning condition from game end (scrabble)
  * are there points or different degrees of winning that are summed up each round (poker, hearts)?
    * possible that they are not summed, but multiplied or maximized or something else crazy
  * min vs max
## References to real world or nongame objects
  * fishbowl
  * taboo
  * codenames
## Significance of guessing/predicting hidden information
  * common among simple word-based games
  * generally requires real world knowledge but not necessarily
  * fishbowl
  * taboo
  * codenames
  * could have structure (scrabble, codenames)
  * or not (taboo)
  * just dependent on fixed-set vocabulary (scrabble, bananagrams) or larger knowledge of language (taboo, codenames)
## Memory component
  * is memorizing information important? How important?
    * could be important for improving strategy or knowing probabilities of future revealed information (poker, hearts)
    * could be central to the game (fishbowl)

## Playing against dealer
  * Dealer could be a nonstrategic randomized algorithm that tends to oppose goals of players
    * common in RPG video games
    * Pandemic

## Importance of randomness
  * is there randomness throughout game?
  * are there fixed random seeds at start of game or round (poker)
  * or added randomness as game progresses as well (pandemic - reshuffling of infection deck)
  * does randomness affect rules as game proceeds (pandemic - selecting event cards)
## Other strategic elements
  * is strategy determined by dealt tokens at start of game (hearts)
  * or dealt tokens as game progresses (poker, pandemic)
  * or fixed based on layout of game board (go, chess, tic tac toe, connect 4)