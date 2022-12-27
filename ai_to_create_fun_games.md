## AI To Create Fun Games for Humans

A fun game is one that requires some level of mental effort but not too much.
Different games require different types or levels of effort, and appeal to different audiences


# Types of effort required
* short term memory- STM (fishbowl)
  * time component
* well-indexed long term memory LTM (scrabble)
* lookahead (chess)
* strategic intuition based on approximate rules (go)
* psychological manipulation (catan, poker, secret hitler)
  * alliances, trade, lying, bluffing
* mathematical computation
  * sometimes very similar to memory, as in computing probabilities in Poker. 
  * but in poker there's also determining levels of confidence in your hand based on imperfect info
  * In hearts or high-low poker there's a choice of strategy based on probability of winning each given your hand (2 different & competing winning conditions)
* real world knowledge (taboo, codenames)
* word/token association (codenames, set)
* quick association
    * verbal (taboo)
    * visual (set)

# Quantifying Fun
In each case, you can determine a numeric level of complexity/hardness/effort by learning an AI to play the game (e.g. using self-play+NN+tree search like AlphaZero) with a fixed number of parameters in the model and fixed amount of online lookahead.
The number of computational cycles needed to bring the model to convergence, possibly coupled with the cycles & memory needed online during gameplay, is a proxy for complexity (and hence fun) of the game.
I imagine that for each human, there is a graph that can be drawn of complexity (= weighted sum of training & online comp. cyles & memory for given # of parameters used to train and play) vs. perceived fun.
Graph would likely be a convex structure with a single maximum. Left side would end at a fixed point (= 0 complexity, 0 fun) and right would asymptote at fun=0 as complexity approaches infinity

However, the above way of quantifying complexity does not work for games that rely heavily on quick short term memory with an easy structure- like Set. For it to work with Set, the algorithm would have to learn purely from pixels as in DeepMind's Atari players. The abstract Set game is exceedingly easy for a computer, but the addition of needing to find tokens distributed at random visually lends a much harder challenge

Given the varying types of effort described above, there could be several proxy metrics created. I'm not sure how to separate complexity metrics in the way described above into for instance psychological manipulation with imperfect info, vs pure lookahead. Both would require a large online component to the AI (e.g. monte carlo tree search with significant number of lookahead steps). Perhaps would would separate them is the size of the offline model (larger in poker than chess, even though online model is similar). Distinguishing games that require real world or verbal knowledge from those that are based purely on game abstraction is easy. To train it, do you need to include a large language model (taboo, codenames)? Or based on visual cues (need a model that learns from pixels)? Not sure how to distinguish complexity involved in predicting unknown information just from complexity/memory/runtime quantifiers. Maybe the structure of learning algorithm is necessarily different. Poker algo has to search through many unknown variations of the current state of the game (what hands are possible for each player), while Chess/Go only have to search through the current, known state of the game. What is the percentage of CPU cycles or memory spent on training this portion? Same with psychological manipulation- complexity can involve interactions with other players. What percentage of training time is spent searching through or optimizing weights for the part of the bot that controls interactions with other players (interactions could be information sharing, perceived or precisely defined in gameplay, or actual game board alteration via e.g. trade)

# Parameter tuning of games
Games generally have lots of fixed (hyper)parameters that provide a great measure of control over the overall complexity. For instance, number of cards in your hand in poker, size of board in Go, number of spaces and direction pawns can move in Chess. Given the above criterion for quantifying fun, it should be possible to optimize a game's hyperparameters to create the most fun for a specific type of player. Using existing games that are known to be fun to certain types of players already (types of players could be age, or those that like verbal association, or psychological manipulation), find out the complexity criteria defined above by learning algorithms to play them well (again, given fixed set of parameters & amount of online lookahead in the model to allow generalization across games and models). Then, do a hyperparameter search, perhaps a better-than-random algorithm can be used to do this (another meta neural network?) on the space of parameters to optimize for particular levels of complexity. In this way, you could find the best version of chess for 4-6 year olds. Or modify the number of political parties in Secret Hitler to make the game more challenging. You could also use this to figure out if your newly created amazing game is actually fun to play, and which settings of parameters make it so.

# More Meta: AI Creation of Games Themselves
What if games could be sufficiently abstracted to allow for the modifications of the rules themselves by a neural network or other AI system trained on existing games? This is a supervised learning problem, where the inputs are abstractions of games, and outputs are complexity or fun levels of those games. I would guess there are on the order of thousands of examples of "fun" real world games that humans like to play. Each one could be given a nonzero fun or complexity score using the above method. Furthermore, large amounts of additional training data can be manufactured by subtly altering the parameters of the game and using the methods described above to attach complexity measurements to those modified games. It's unclear whether these additional games would also be fun, but we can perhaps assume they are given that they have very similar rules/structure to existing games.

Once a training set is collected, a recommendation algorithm can be learned to suggest novel games by creating rulesets, and determining their predicted level of fun. Or, perhaps a semirandom search of rules can be fed into a supervised regressor, and its outputs used to filter which ones are fun. This can be used to bootstrap better versions of the algorithm in an RL/self-play kind of way. Probably an online, human labeled component is needed for this to work effectively. Newly created games are randomly selected and played by human labelers who give some ratings of perceived fun or difficulty.

Ways of defining game abstractions is brainstormed in the other markdown.