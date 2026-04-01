# Moving average

> **Source:** [Wikipedia — Moving average](https://en.wikipedia.org/wiki/Moving_average)
> **Category:** Assigned during local extraction

In statistics, a moving average (rolling average or running average or moving mean or rolling mean) is a calculation to analyze data points by creating a series of averages of different selections of the full data set. Variations include: simple, cumulative, or weighted forms.
Mathematically, a moving average is a type of convolution. Thus in signal processing it is viewed as a low-pass finite impulse response filter. Because the boxcar function outlines its filter coefficients, it is called a boxcar filter. It is sometimes followed by downsampling.
Given a series of numbers and a fixed subset size, the first element of the moving average is obtained by taking the average of the initial fixed subset of the number series. Then the subset is modified by "shifting forward"; that is, excluding the first number of the series and including the next value in the series.
A moving average is commonly used with time series data to smooth out short-term fluctuations and highlight longer-term trends or cycles - in this case the calculation is sometimes called a time average. The threshold between short-term and long-term depends on the application, and the parameters of the moving average will be set accordingly. It is also used in economics to examine gross domestic product, employment or other macroeconomic time series. When used with non-time series data, a moving average filters higher frequency components without any specific connection to time, although typically some kind of ordering is implied. Viewed simplistically it can be regarded as smoothing the data.

## History

The technique of moving averages was invented by the Bank of England in 1833 to conceal the state of its bullion reserves.

## Simple moving average

In financial applications a simple moving average (SMA) is the unweighted mean of the previous 
  
    
      
        k
      
    
    {\displaystyle k}
  
 data-points. However, in science and engineering, the mean is normally taken from an equal number of data on either side of a central value. This ensures that variations in the mean are aligned with the variations in the data rather than being shifted in time. An example of a simple equally weighted running mean is the mean over the last 
  
    
      
        k
      
    
    {\displaystyle k}
  
 entries of a data-set containing 
  
    
      
        n
      
    
    {\displaystyle n}
  
 entries. Let those data-points be 
  
    
      
        
          p
          
            1
          
        
        ,
        
          p
          
            2
          
        
        ,
        …
        ,
        
          p
          
            n
          
        
      
    
    {\displaystyle p_{1},p_{2},\dots ,p_{n}}
  
. This could be closing prices of a stock. The mean over the last 
  
    
      
        k
      
    
    {\displaystyle k}
  
 data-points (days in this example) is denoted as 
  
    
      
        
          
            
              SMA
            
          
          
            k
          
        
      
    
    {\displaystyle {\textit {SMA}}_{k}}
  
 and calculated as:

  
    
      
        
          
            
              
                
                  
                    
                      SMA
                    
                  
                  
                    k
                  
                
              
              
                
                =
                
                  
                    
                      
                        p
                        
                          n
                          −
                          k
                          +
                          1
                        
                      
                      +
                      
                        p
                        
                          n
                          −
                          k
                          +
                          2
                        
                      
                      +
                      ⋯
                      +
                      
                        p
                        
                          n
                        
                      
                    
                    k
                  
                
              
            
            
              
              
                
                =
                
                  
                    1
                    k
                  
                
                
                  ∑
                  
                    i
                    =
                    n
                    −
                    k
                    +
                    1
                  
                  
                    n
                  
                
                
                  p
                  
                    i
                  
                
              
            
          
        
      
    
    {\displaystyle {\begin{aligned}{\textit {SMA}}_{k}&={\frac {p_{n-k+1}+p_{n-k+2}+\cdots +p_{n}}{k}}\\&={\frac {1}{k}}\sum _{i=n-k+1}^{n}p_{i}\end{aligned}}}
  

When calculating the next mean 
  
    
      
        
          
            
              SMA
            
          
          
            k
            ,
            
              next
            
          
        
      
    
    {\displaystyle {\textit {SMA}}_{k,{\text{next}}}}
  
 with the same sampling width 
  
    
      
        k
      
    
    {\displaystyle k}
  
 the range from 
  
    
      
        n
        −
        k
        +
        2
      
    
    {\displaystyle n-k+2}
  
 to 
  
    
      
        n
        +
        1
      
    
    {\displaystyle n+1}
  
 is considered. A new value 
  
    
      
        
          p
          
            n
            +
            1
          
        
      
    
    {\displaystyle p_{n+1}}
  
 comes into the sum and the oldest value 
  
    
      
        
          p
          
            n
            −
            k
            +
            1
          
        
      
    
    {\displaystyle p_{n-k+1}}
  
 drops out. This simplifies the calculations by reusing the previous mean 
  
    
      
        
          
            
              SMA
            
          
          
            k
            ,
            
              prev
            
          
        
      
    
    {\displaystyle {\textit {SMA}}_{k,{\text{prev}}}}
  
.

  
    
      
        
          
            
              
                
                  
                    
                      SMA
                    
                  
                  
                    k
                    ,
                    
                      next
                    
                  
                
              
              
                
                =
                
                  
                    1
                    k
                  
                
                
                  ∑
                  
                    i
                    =
                    n
                    −
                    k
                    +
                    2
                  
                  
                    n
                    +
                    1
                  
                
                
                  p
                  
                    i
                  
                
              
            
            
              
              
                
                =
                
                  
              

*(section truncated for brevity)*

## Continuous moving average

The continuous moving average of an integrable function 
  
    
      
        f
        :
        
          R
        
        →
        
          R
        
      
    
    {\displaystyle f:\mathbb {R} \rightarrow \mathbb {R} }
  
 is defined via integration as:

  
    
      
        
          
            
              
                
                  M
                  
                    f
                    ,
                    ε
                  
                
                :
                
                  R
                
              
              
                →
                
                  R
                
              
            
            
              
                x
              
              
                ↦
                
                  
                    
                      1
                      
                        2
                        
                        ε
                      
                    
                  
                  
                    ∫
                    
                      x
                      −
                      ε
                    
                    
                      x
                      +
                      ε
                    
                  
                  f
                  (
                  t
                  )
                  
                  d
                  t
                
              
            
          
        
      
    
    {\displaystyle {\begin{array}{rl}M_{f,\varepsilon }:\mathbb {R} &\rightarrow \mathbb {R} \\x&\mapsto \displaystyle {\frac {1}{2\,\varepsilon }}\int _{x-\varepsilon }^{x+\varepsilon }f(t)\,dt\end{array}}}
  

where the 
  
    
      
        ε
      
    
    {\displaystyle \varepsilon }
  
 environment 
  
    
      
        [
        x
        −
        ε
        ,
        x
        +
        ε
        ]
      
    
    {\displaystyle [x-\varepsilon ,x+\varepsilon ]}
  
 around 
  
    
      
        x
      
    
    {\displaystyle x}
  
 defines the intensity of smoothing of the graph of the integrable function. A larger 
  
    
      
        ε
        >
        0
      
    
    {\displaystyle \varepsilon >0}
  
 smooths the source graph of the function (blue) 
  
    
      
        f
      
    
    {\displaystyle f}
  
 more. The animations below show the moving average as animation in dependency of different values for  
  
    
      
        ε
        >
        0
      
    
    {\displaystyle \varepsilon >0}
  
. The fraction 
  
    
      
        
          
            1
            
              2
              
              ε
            
          
        
      
    
    {\displaystyle {\frac {1}{2\,\varepsilon }}}
  
 is used, because 
  
    
      
        2
        
        ε
      
    
    {\displaystyle 2\,\varepsilon }
  
 is the interval width for the integral. Naturally, 
  
    
      
        
          lim
          
            ε
            →
            0
          
        
        
          M
          
            f
            ,
             
            ε
          
        
        =
        f
      
    
    {\displaystyle \lim _{\varepsilon \to 0}M_{f,\ \varepsilon }=f}
  
 by fundamental theorem of calculus and L'Hôpital's rule.

## Cumulative average

In a cumulative average (CA), the data arrive in an ordered datum stream, and the user would like to get the average of all of the data up until the current datum. For example, an investor may want the average price of all of the stock transactions for a particular stock up until the current time. As each new transaction occurs, the average price at the time of the transaction can be calculated for all of the transactions up to that point using the cumulative average, typically an equally weighted average of the sequence of n values 
  
    
      
        
          x
          
            1
          
        
        .
        …
        ,
        
          x
          
            n
          
        
      
    
    {\displaystyle x_{1}.\ldots ,x_{n}}
  
 up to the current time:

  
    
      
        
          
            
              CA
            
          
          
            n
          
        
        =
        
          
            
              
                x
                
                  1
                
              
              +
              ⋯
              +
              
                x
                
                  n
                
              
            
            n
          
        
        
        .
      
    
    {\displaystyle {\textit {CA}}_{n}={{x_{1}+\cdots +x_{n}} \over n}\,.}
  

The brute-force method to calculate this would be to store all of the data and calculate the sum and divide by the number of points every time a new datum arrived. However, it is possible to simply update cumulative average as a new value, 
  
    
      
        
          x
          
            n
            +
            1
          
        
      
    
    {\displaystyle x_{n+1}}
  
 becomes available, using the formula

  
    
      
        
          
            
              CA
            
          
          
            n
            +
            1
          
        
        =
        
          
            
              
                x
                
                  n
                  +
                  1
                
              
              +
              n
              ⋅
              
                
                  
                    CA
                  
                
                
                  n
                
              
            
            
              n
              +
              1
            
          
        
        .
      
    
    {\displaystyle {\textit {CA}}_{n+1}={{x_{n+1}+n\cdot {\textit {CA}}_{n}} \over {n+1}}.}
  

Thus the current cumulative average for a new datum is equal to the previous cumulative average, times n, plus the latest datum, all divided by the number of points received so far, n+1. When all of the data arrive (n = N), then the cumulative average will equal the final average. It is also possible to store a running total of the data as well as the number of points and dividing the total by the number of points to get the CA each time a new datum arrives.
The derivation of the cumulative average formula is straightforward. Using

  
    
      
        
          x
          
            1
          
        
        +
        ⋯
        +
        
          x
          
            n
          
        
        =
        n
        ⋅
        
          
            
              CA
            
          
          
            n
          
        
      
    
    {\displaystyle x_{1}+\cdots +x_{n}=n\cdot {\textit {CA}}_{n}}
  

and similarly for n + 1, it is seen that

  
    
      
        
          x
          
            n
            +
            1
          
        
        =
        (
        
          x
          
            1
          
        
        +
        ⋯
        +
        
          x
          
            n
            +
            1
          
        
        )
        −
        (
        
          x
          
            1
          
        
        +
        ⋯
        +
        
          x
          
            n
          
        
        )
      
    
    {\displaystyle x_{n+1}=(x_{1}+\cdots +x_{n+1})-(x_{1}+\cdots +x_{n})}
  

  
    
      
        
          x
          
            n
            +
            1
          
        
        =
        (
        n
        +
        1
        )
        ⋅
        
          
            
              CA
            
          
          
            n
            +
            1
          
        
        −
        n
        ⋅
        
          
            
              CA
            
          
          
            n
          
        
      
    
    {\displaystyle x_{n+1}=(n+1)\cdot {\textit {CA}}_{n+1}-n\cdot {\textit {CA}}_{n}}
  

Solving this equation for 
  
    
      
        
          
            
              CA
            
          
          
            n
            +
            1
          
        
      
    
    {\displaystyle {\textit {CA}}_{n+1}}
  
 results in

  
    
      
        
          
            
              
                
                  
                    
                      CA
                    
                  
                  
                    n
                    +
                    1
                  
                
              
              
                
                =
                
                  
                    
                      
                        x
                        
                          n
                          +
                          1
                        
                      
                      +
                      n
                      ⋅
                      
                        
                          
                            CA
                          
                        
                        
                          n
                        
         

*(section truncated for brevity)*

## Weighted moving average

A weighted average is an average that has multiplying factors to give different weights to data at different positions in the sample window. Mathematically, the weighted moving average is the convolution of the data with a fixed weighting function. One application is removing pixelization from a digital graphical image. This is also known as Anti-aliasing 
In the financial field, and more specifically in the analyses of financial data, a weighted moving average (WMA) has the specific meaning of weights that decrease in arithmetical progression. In an n-day WMA the latest day has weight n, the second latest 
  
    
      
        n
        −
        1
      
    
    {\displaystyle n-1}
  
, etc., down to one.

  
    
      
        
          
            WMA
          
          
            M
          
        
        =
        
          
            
              n
              
                p
                
                  M
                
              
              +
              (
              n
              −
              1
              )
              
                p
                
                  M
                  −
                  1
                
              
              +
              ⋯
              +
              2
              
                p
                
                  (
                  (
                  M
                  −
                  n
                  )
                  +
                  2
                  )
                
              
              +
              
                p
                
                  (
                  (
                  M
                  −
                  n
                  )
                  +
                  1
                  )
                
              
            
            
              n
              +
              (
              n
              −
              1
              )
              +
              ⋯
              +
              2
              +
              1
            
          
        
      
    
    {\displaystyle {\text{WMA}}_{M}={np_{M}+(n-1)p_{M-1}+\cdots +2p_{((M-n)+2)}+p_{((M-n)+1)} \over n+(n-1)+\cdots +2+1}}
  

The denominator is a triangle number equal to 
  
    
      
        
          
            
              n
              (
              n
              +
              1
              )
            
            2
          
        
        .
      
    
    {\textstyle {\frac {n(n+1)}{2}}.}
  
 In the more general case the denominator will always be the sum of the individual weights.
When calculating the WMA across successive values, the difference between the numerators of 
  
    
      
        
          
            WMA
          
          
            M
            +
            1
          
        
      
    
    {\displaystyle {\text{WMA}}_{M+1}}
  
 and 
  
    
      
        
          
            WMA
          
          
            M
          
        
      
    
    {\displaystyle {\text{WMA}}_{M}}
  
 is 
  
    
      
        n
        
          p
          
            M
            +
            1
          
        
        −
        
          p
          
            M
          
        
        −
        ⋯
        −
        
          p
          
            M
            −
            n
            +
            1
          
        
      
    
    {\displaystyle np_{M+1}-p_{M}-\dots -p_{M-n+1}}
  
. If we denote the sum 
  
    
      
        
          p
          
            M
          
        
        +
        ⋯
        +
        
          p
          
            M
            −
            n
            +
            1
          
        
      
    
    {\displaystyle p_{M}+\dots +p_{M-n+1}}
  
 by 
  
    
      
        
          
            Total
          
          
            M
          
        
      
    
    {\displaystyle {\text{Total}}_{M}}
  
, then

  
    
      
        
          
            
              
                
                  
                    Total
                  
                  
                    M
                    +
                    1
                  
                
              
              
                
                =
                
                  
                    Total
                  
                  
                    M
                  
                
                +
                
                  p
                  
                    M
                    +
                    1
                  
                
                −
                
                  p
                  
                    M
                    −
                    n
                    +
                    1
                  
                
              
            
            
              
                
                  
                    Numerator
                  
                  
                    M
                    +
                    1
                  
                
              
              
                
                =
                
                  
                    Numerator
                  
                  
                    M
                  
                
                +
                n
                
                  p
                  
                    M
                    +
                    1
                  
                
                −
                
                  
                    Total
                  
                  
                    M
                  
                
              
            
            
              
                
                  
                    WMA
                  
                  
                    M
                    +
                    1
                  
                
              


*(section truncated for brevity)*

## Exponential moving average

An exponential moving average (EMA), also known as an exponentially weighted moving average (EWMA), is a first-order infinite impulse response filter that applies weighting factors which decrease exponentially. The weighting for each older datum decreases exponentially, never reaching zero. 
This formulation is according to Hunter (1986).
There is also a multivariate implementation of EWMA, known as MEWMA.

## Other weightings

Other weighting systems are used occasionally – for example, in share trading a volume weighting will weight each time period in proportion to its trading volume.
A further weighting, used by actuaries, is Spencer's 15-Point Moving Average (a central moving average). Its symmetric weight coefficients are [−3, −6, −5, 3, 21, 46, 67, 74, 67, 46, 21, 3, −5, −6, −3], which factors as ⁠[1, 1, 1, 1]×[1, 1, 1, 1]×[1, 1, 1, 1, 1]×[−3, 3, 4, 3, −3]/320⁠ and leaves samples of any quadratic or cubic polynomial unchanged.
Outside the world of finance, weighted running means have many forms and applications. Each weighting function or "kernel" has its own characteristics. In engineering and science the frequency and phase response of the filter is often of primary importance in understanding the desired and undesired distortions that a particular filter will apply to the data.
A mean does not just "smooth" the data. A mean is a form of low-pass filter. The effects of the particular filter used should be understood in order to make an appropriate choice.

## Moving median

From a statistical point of view, the moving average, when used to estimate the underlying trend in a time series, is susceptible to rare events such as rapid shocks or other anomalies. A more robust estimate of the trend is the simple moving median over n time points:

  
    
      
        
          
            
              
                p
                ~
              
            
          
          
            SM
          
        
        =
        
          Median
        
        (
        
          p
          
            M
          
        
        ,
        
          p
          
            M
            −
            1
          
        
        ,
        …
        ,
        
          p
          
            M
            −
            n
            +
            1
          
        
        )
      
    
    {\displaystyle {\widetilde {p}}_{\text{SM}}={\text{Median}}(p_{M},p_{M-1},\ldots ,p_{M-n+1})}
  

where the median is found by, for example, sorting the values inside the brackets and finding the value in the middle.  For larger values of n, the median can be efficiently computed by updating an indexable skiplist.
Statistically, the moving average is optimal for recovering the underlying trend of the time series when the fluctuations about the trend are normally distributed. However, the normal distribution does not place high probability on very large deviations from the trend which explains why such deviations will have a disproportionately large effect on the trend estimate. It can be shown that if the fluctuations are instead assumed to be Laplace distributed, then the moving median is statistically optimal. For a given variance, the Laplace distribution places higher probability on rare events than does the normal, which explains why the moving median tolerates shocks better than the moving mean.
When the simple moving median above is central, the smoothing is identical to the median filter which has applications in, for example, image signal processing. The Moving Median is a more robust alternative to the Moving Average when it comes to estimating the underlying trend in a time series. While the Moving Average is optimal for recovering the trend if the fluctuations around the trend are normally distributed, it is susceptible to the impact of rare events such as rapid shocks or anomalies. In contrast, the Moving Median, which is found by sorting the values inside the time window and finding the value in the middle, is more resistant to the impact of such rare events. This is because, for a given variance, the Laplace distribution, which the Moving Median assumes, places higher probability on rare events than the normal distribution that the Moving Average assumes. As a result, the Moving Median provides a more reliable and stable estimate of the underlying trend even when the time series is affected by large deviations from the trend. Additionally, the Moving Median smoothing is identical to the Median Filter, which has various applications in image signal processing.

## Moving average regression model

In a moving average regression model, a variable of interest is assumed to be a weighted moving average of unobserved independent error terms; the weights in the moving average are parameters to be estimated.
Those two concepts are often confused due to their name, but while they share many similarities, they represent distinct methods and are used in very different contexts.