```
     _____ ___________ _____ _____ _____  ___  ___  _____  _   __
    /  ___|_   _| ___ \  ___|  ___|_   _||_  |/ _ \/  __ \| | / /
    \ `--.  | | | |_/ / |__ | |__   | |    | / /_\ \ /  \/| |/ / 
     `--. \ | | |    /|  __||  __|  | |    | |  _  | |    |    \ 
    /\__/ / | | | |\ \| |___| |___  | |/\__/ / | | | \__/\| |\  \
    \____/  \_/ \_| \_\____/\____/  \_/\____/\_| |_/\____/\_| \_/
```

<hr>

Streetjack is a poker bot for playing heads up limited Texas Hold'em. It makes use of the  <b>counterfactual regret minimisation algorithm</b> (which implies a technique known as <b>no regret learning</b>) and game abstractions such as bucketing based on hand potential. The game can be played on a terminal device only.

## :black_joker: What is heads up limited Texas Hold'em (aka HULTH)?

It is a version of Texas Hold'em which follows the same rules in terms of stages, hand ranking, etc. The difference is that:

- it is played by only 2 players at a time
- the raise amounts are limitted to a fixed number

In regular poker you have `13,484,135,099,635,200,000` states while in HULTH there are 3.16 ∗ 10<sup>17</sup> states. This drastically reduces the memory constraints of the game.

## :thinking: Still too many game states to fit on your disk?

Don't worry we've though about this. `Streetjack` exploits a technique of grouping multiple equivalent game nodes from a players point of view. But what does "equivalent" mean??? It means that a player would not notice the difference between such nodes with the information he/she knows which is:

- the game history as a sequence of actions until the game state
- his/her private cards
- the public cards
- the player bets (which can be derived from the history)

We call these equivalence classes <b>information sets</b>. In a game of HULTH there are 3.19 ∗ 10<sup>14</sup> which is another major reduction.

## Bucketing

Another optimisation that `streetjack` has is to additionally group information sets into equivalence classes called <b>buckets</b>. This is done by calculating a metric called hand potential which is equal to the probability of your hand becoming strong. For single hand the <b>Chen formula</b> is used while for >= 5 cards the <b>Effective Hand Strength algorithm</b>.

## 🧠 How come is streetjack so smart?

It uses an algorith called <b>Counterfactual Regret Minimisation</b> which is a type of a no regret learning algorithm. It is used because it performs pretty well on:

- imperfect information games
- zero sum games
- stochastic games

and HULTH is definitely one of them! As the name suggests it is based on regrets. Imagine the following scenario - you are about to take your turn and have the option to raise, check or fold. Each action leads to a different outcome and according to the end utility you regret playing some more than others. Hence next time your <b>strategy</b> when picking one of them would've changed.

OK! But what is strategy? It is nothing more than the probability distribution of selecting particular actions the next time you play in an information set. The strategies of all players form a set that is called a strategy profile. A good strategy profile is one for which a state called ε-Nash equilibrium is reached which means that if one strategy in a given profile is replaced by another it (most probably) cannot provide better results. A strategy within a ε-Nash equilibrium strategy profile is usually called a defensive strategy.

## Useful docs

- [How to use streejack?](/docs/user_guide.md)
- [Contribution guide](/docs/contribution.md)
